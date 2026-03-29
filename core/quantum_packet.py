"""Quantum wave packet simulation engine.

Emits discrete wave packets from the laser that propagate along the optical
network, split at beam splitters, and are detected probabilistically at
detectors according to wave optics predictions.
"""

import logging
import random
import time
import math
import cmath
from enum import Enum
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Set, Tuple
from utils.vector import Vector2

logger = logging.getLogger(__name__)


class PacketState(Enum):
    TRAVELING = "traveling"
    ARRIVED = "arrived"        # reached a detector, waiting for siblings
    DETECTED = "detected"      # this packet's detector clicked
    COLLAPSED = "collapsed"    # this packet's path was not taken
    EXPIRED = "expired"        # hit edge / block


@dataclass
class QuantumPacket:
    """A single wave packet (or sub-packet after splitting)."""
    id: int
    family_id: int
    connection_index: int          # index into wave engine connections list
    path: List[Vector2]            # waypoints for this connection
    progress: float = 0.0         # 0..1 along the full path
    amplitude: complex = 1.0+0j
    state: PacketState = PacketState.TRAVELING
    creation_time: float = 0.0
    detection_time: float = 0.0   # when state changed to DETECTED/COLLAPSED
    detector: object = None       # detector component if arrived
    trail_points: List[Vector2] = field(default_factory=list)
    # for collapse animation — full history of visited connections
    history_paths: List[List[Vector2]] = field(default_factory=list)
    generation: int = 0            # splitting depth (limits feedback loops)
    photon_idx: int = 0            # which photon within a multi-photon pulse


class PacketFamily:
    """Groups all sub-packets originating from one emission event.

    For multi-photon pulses each photon is identified by its
    ``photon_idx`` (0 … n_photons-1).  Detection resolves each photon
    independently so that coincidence statistics can be accumulated.
    """

    def __init__(self, family_id: int, n_photons: int = 1):
        self.family_id = family_id
        self.n_photons = n_photons
        self.packets: List[QuantumPacket] = []
        self.detected = False
        self.detected_detector = None       # first detected (back-compat)
        self.detected_detectors: List = []  # one per photon_idx
        self.detection_time: float = 0.0
        self.collapsed_time: float = 0.0
        self.fully_resolved = False   # all packets in terminal state

    def add_packet(self, packet: QuantumPacket):
        self.packets.append(packet)

    def all_terminal(self) -> bool:
        return all(p.state in (PacketState.ARRIVED, PacketState.DETECTED,
                               PacketState.COLLAPSED, PacketState.EXPIRED)
                   for p in self.packets)

    def all_done(self) -> bool:
        """All packets finished animation."""
        return all(p.state in (PacketState.DETECTED, PacketState.COLLAPSED,
                               PacketState.EXPIRED)
                   for p in self.packets)


class QuantumPacketEngine:
    """Manages emission, propagation, splitting, and detection of wave packets."""

    _next_packet_id = 0
    _next_family_id = 0

    def __init__(self):
        self.families: List[PacketFamily] = []
        self.emit_timer: float = 0.0
        self.emit_interval: float = 1.5   # seconds between emissions
        self.packet_speed: float = 200.0   # pixels per second
        self.max_families: int = 12
        self.collapse_duration: float = 0.3  # seconds
        self.photons_per_pulse: int = 1    # number of photons per emission
        self._network_graph: Optional[Dict] = None
        self._graph_fingerprint: Optional[Tuple] = None
        self._detection_counts: Dict[object, int] = {}  # detector -> count
        self._total_detections: int = 0
        # Coincidence counting: frozenset of detectors → count
        self._coincidence_counts: Dict[frozenset, int] = {}
        # Photon-number-resolved (PNR) counting: detector → {n_photons → count}
        self._pnr_counts: Dict[object, Dict[int, int]] = {}
        self._total_pulses: int = 0
        self.on_detection = None  # callback(detector) for sound etc.

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def reset(self):
        self.families.clear()
        self.emit_timer = 0.0
        self._network_graph = None
        self._graph_fingerprint = None
        self._detection_counts.clear()
        self._total_detections = 0
        self._coincidence_counts.clear()
        self._pnr_counts.clear()
        self._total_pulses = 0

    def reset_histogram(self):
        self._detection_counts.clear()
        self._total_detections = 0
        self._coincidence_counts.clear()
        self._pnr_counts.clear()
        self._total_pulses = 0

    def get_theoretical_probs(self) -> Dict:
        """Return {detector: probability} from wave optics solution."""
        if not self._network_graph:
            return {}
        det_amps: Dict[object, complex] = {}
        for conn in self._network_graph['connections']:
            if conn['dest_component'].component_type == 'detector':
                det = conn['dest_component']
                det_amps.setdefault(det, 0j)
                det_amps[det] += conn['amplitude']
        total = sum(abs(a) ** 2 for a in det_amps.values())
        if total < 1e-10:
            return {}
        return {det: abs(a) ** 2 / total for det, a in det_amps.items()}

    def update(self, dt: float, wave_engine):
        """Advance all packets and handle emissions."""
        # Rebuild graph only when topology changes
        fingerprint = None
        if hasattr(wave_engine, 'connections') and wave_engine.connections:
            fingerprint = (len(wave_engine.connections),
                           tuple(id(c.port1.component) for c in wave_engine.connections),
                           tuple(id(c.port2.component) for c in wave_engine.connections))
        if fingerprint != self._graph_fingerprint:
            self._network_graph = self._build_graph(wave_engine)
            self._graph_fingerprint = fingerprint

        if not self._network_graph or not self._network_graph['laser_connections']:
            return

        # Emission timer
        self.emit_timer += dt
        if self.emit_timer >= self.emit_interval:
            self.emit_timer -= self.emit_interval
            if len(self.families) < self.max_families:
                self._emit_packet()

        now = time.time()

        # Propagate
        for family in self.families:
            if family.fully_resolved:
                continue
            self._propagate_family(family, dt, now)

        # Clean up old families
        self._cleanup(now)

    def get_detection_stats(self) -> Dict:
        """Return {detector: (count, fraction)} for histogram."""
        result = {}
        for det, count in self._detection_counts.items():
            frac = count / self._total_detections if self._total_detections > 0 else 0
            result[det] = (count, frac)
        return result

    def get_coincidence_stats(self) -> Dict:
        """Return {frozenset_of_detectors: (count, rate)} for coincidence display."""
        result = {}
        for key, count in self._coincidence_counts.items():
            rate = count / self._total_pulses if self._total_pulses > 0 else 0
            result[key] = (count, rate)
        return result

    def get_pnr_stats(self) -> Dict:
        """Return photon-number-resolved statistics per detector.

        Returns
        -------
        dict
            ``{detector: {n_photons: (count, rate)}}`` where *rate* is
            the fraction of pulses that deposited exactly *n_photons*
            photons at that detector.  ``n_photons = 0`` entries are
            included so the distribution is complete.
        """
        if self._total_pulses < 1:
            return {}
        result: Dict[object, Dict[int, Tuple[int, float]]] = {}
        # Collect all detectors that have ever fired
        all_dets = set(self._pnr_counts.keys())
        for det in all_dets:
            dist = self._pnr_counts[det]
            n_max = max(dist.keys()) if dist else 0
            det_result: Dict[int, Tuple[int, float]] = {}
            fired_pulses = sum(dist.values())
            zero_count = self._total_pulses - fired_pulses
            if zero_count > 0:
                det_result[0] = (zero_count, zero_count / self._total_pulses)
            for n, count in sorted(dist.items()):
                det_result[n] = (count, count / self._total_pulses)
            result[det] = det_result
        return result

    # ------------------------------------------------------------------
    # Emission
    # ------------------------------------------------------------------

    def _emit_packet(self):
        fid = QuantumPacketEngine._next_family_id
        QuantumPacketEngine._next_family_id += 1
        n = self.photons_per_pulse
        family = PacketFamily(fid, n_photons=n)

        graph = self._network_graph
        for photon_idx in range(n):
            for conn_idx in graph['laser_connections']:
                conn_info = graph['connections'][conn_idx]
                pkt = self._make_packet(fid, conn_idx, conn_info,
                                        amplitude=1.0+0j,
                                        photon_idx=photon_idx)
                family.add_packet(pkt)

        self.families.append(family)

    def _make_packet(self, family_id, conn_idx, conn_info, amplitude,
                     generation=0, photon_idx=0):
        pid = QuantumPacketEngine._next_packet_id
        QuantumPacketEngine._next_packet_id += 1
        path = conn_info['path']
        return QuantumPacket(
            id=pid,
            family_id=family_id,
            connection_index=conn_idx,
            path=path,
            progress=0.0,
            amplitude=amplitude,
            state=PacketState.TRAVELING,
            creation_time=time.time(),
            trail_points=[],
            history_paths=[],
            generation=generation,
            photon_idx=photon_idx,
        )

    # ------------------------------------------------------------------
    # Propagation
    # ------------------------------------------------------------------

    def _propagate_family(self, family: PacketFamily, dt: float, now: float):
        new_packets: List[QuantumPacket] = []

        # Collect packets that arrive at beam splitters this frame so we can
        # batch multi-photon arrivals for Fock-state processing.
        # Key: id(dest_component) → list of (packet, conn_info, dest_component)
        bs_arrivals: Dict[int, List[Tuple]] = {}

        for pkt in family.packets:
            if pkt.state != PacketState.TRAVELING:
                continue

            conns = self._network_graph['connections']
            if pkt.connection_index >= len(conns):
                pkt.state = PacketState.EXPIRED
                continue
            conn_info = conns[pkt.connection_index]
            length = conn_info['length']
            if length < 1:
                length = 1

            # Advance progress
            speed_frac = (self.packet_speed * dt) / length
            pkt.progress += speed_frac

            # Record trail with distance-based sampling
            pos = self._get_packet_position(pkt)
            if pos is not None:
                if not pkt.trail_points or pos.distance_to(pkt.trail_points[-1]) > 3:
                    pkt.trail_points.append(pos)
                    # Decimate if trail gets too long
                    if len(pkt.trail_points) > 150:
                        pkt.trail_points = pkt.trail_points[::2][:75] + pkt.trail_points[75:]

            if pkt.progress >= 1.0:
                pkt.progress = 1.0
                # Apply propagation phase for this connection
                pkt.amplitude *= cmath.exp(1j * conn_info['phase_shift'])
                # Save this connection's path to history
                pkt.history_paths.append(list(pkt.path))
                # Packet reached end of connection
                dest_comp = conn_info['dest_component']
                dest_type = dest_comp.component_type

                if dest_type == 'detector':
                    pkt.state = PacketState.ARRIVED
                    pkt.detector = dest_comp
                elif (family.n_photons > 1
                      and hasattr(dest_comp, 'fock_transform')):
                    # Defer BS arrivals for Fock-state batching
                    comp_id = id(dest_comp)
                    bs_arrivals.setdefault(comp_id, []).append(
                        (pkt, conn_info, dest_comp))
                else:
                    # Single-photon or non-BS: classical S-matrix split
                    children = self._split_packet(pkt, conn_info, family.family_id)
                    if children:
                        new_packets.extend(children)
                    else:
                        pkt.state = PacketState.EXPIRED

        # ---- Process batched BS arrivals ----
        for comp_id, arrivals in bs_arrivals.items():
            photon_idxs = set(pkt.photon_idx for pkt, _, _ in arrivals)
            if len(photon_idxs) > 1:
                # Multiple distinct photons at the same BS → Fock state
                children = self._split_packets_fock(arrivals, family.family_id)
                new_packets.extend(children)
            else:
                # Only one photon index present — fall back to classical
                for pkt, conn_info, _ in arrivals:
                    children = self._split_packet(pkt, conn_info, family.family_id)
                    if children:
                        new_packets.extend(children)
                    else:
                        pkt.state = PacketState.EXPIRED

        for child in new_packets:
            family.add_packet(child)

        # Check if all packets have arrived / expired
        if family.all_terminal() and not family.detected:
            self._perform_detection(family, now)

        # Check collapse animation completion
        if family.detected and not family.fully_resolved:
            elapsed = now - family.collapsed_time
            if elapsed > self.collapse_duration:
                for pkt in family.packets:
                    if pkt.state == PacketState.ARRIVED:
                        pkt.state = PacketState.COLLAPSED
                family.fully_resolved = True

    def _get_packet_position(self, pkt: QuantumPacket) -> Vector2:
        """Get current world position of a packet."""
        path = pkt.path
        if not path:
            return Vector2(0, 0)
        if len(path) < 2:
            return path[0]

        # progress 0..1 maps to the full polyline
        total_len = 0
        seg_lengths = []
        for i in range(len(path) - 1):
            sl = path[i].distance_to(path[i+1])
            seg_lengths.append(sl)
            total_len += sl

        if total_len < 0.001:
            return path[0]

        target_dist = pkt.progress * total_len
        accum = 0.0
        for i, sl in enumerate(seg_lengths):
            if accum + sl >= target_dist or i == len(seg_lengths) - 1:
                t = (target_dist - accum) / sl if sl > 0 else 0
                t = max(0, min(1, t))
                p1, p2 = path[i], path[i+1]
                return Vector2(p1.x + t * (p2.x - p1.x),
                               p1.y + t * (p2.y - p1.y))
            accum += sl
        return path[-1]

    # ------------------------------------------------------------------
    # Splitting
    # ------------------------------------------------------------------

    # Maximum splitting depth — prevents infinite feedback loops
    # (e.g. Michelson: BS → mirror → BS → mirror → ...)
    MAX_GENERATION = 8

    def _split_packet(self, pkt: QuantumPacket, conn_info, family_id) -> List[QuantumPacket]:
        """Split packet at a beam splitter / mirror using wave optics amplitudes."""
        # Limit feedback loops
        if pkt.generation >= self.MAX_GENERATION:
            pkt.state = PacketState.EXPIRED
            return []

        graph = self._network_graph
        dest_comp = conn_info['dest_component']

        # Find routing: which outgoing connections from this component?
        routing = graph['component_routing'].get(id(dest_comp), {})
        outgoing_indices = set()
        for out_list in routing.values():
            outgoing_indices.update(out_list)

        if not outgoing_indices:
            return []

        # Get S-matrix of the component
        S = getattr(dest_comp, 'S', None)
        if S is None:
            return []

        input_port_idx = conn_info['dest_port_idx']
        child_gen = pkt.generation + 1

        children = []
        for out_idx in outgoing_indices:
            out_conn = graph['connections'][out_idx]
            output_port_idx = out_conn['source_port_idx']

            # S-matrix coefficient
            s_coeff = S[output_port_idx, input_port_idx]
            if abs(s_coeff) < 1e-6:
                continue

            # S-matrix only — propagation phase is applied when packet
            # finishes traversing its connection in _propagate_family
            child_amplitude = pkt.amplitude * s_coeff

            # Skip children with negligible amplitude
            if abs(child_amplitude) < 0.01:
                continue

            child = self._make_packet(family_id, out_idx, out_conn, child_amplitude,
                                      child_gen, photon_idx=pkt.photon_idx)
            # Inherit history
            child.history_paths = list(pkt.history_paths)
            children.append(child)

        # Mark parent as expired (replaced by children)
        pkt.state = PacketState.EXPIRED
        return children

    # ------------------------------------------------------------------
    # Fock-state splitting
    # ------------------------------------------------------------------

    def _split_packets_fock(self, arrivals, family_id) -> List[QuantumPacket]:
        """Process multiple photons arriving at a BS using Fock-state sampling.

        When two or more photons from the same pulse reach a beam splitter
        simultaneously, their joint output must be sampled from the full
        Fock-state distribution |n,m⟩ → |p,q⟩ rather than treating each
        photon independently.  This correctly reproduces quantum effects
        such as Hong-Ou-Mandel bunching.

        Parameters
        ----------
        arrivals : list of (QuantumPacket, conn_info dict, dest_component)
            All packets that arrived at the *same* beam splitter this frame.
        family_id : int
            Family id for newly created child packets.

        Returns
        -------
        list[QuantumPacket]
        """
        if not arrivals:
            return []

        dest_comp = arrivals[0][2]
        graph = self._network_graph

        # --- Generation limit (same guard as _split_packet) ---
        max_gen = max(pkt.generation for pkt, _, _ in arrivals)
        if max_gen >= self.MAX_GENERATION:
            for pkt, _, _ in arrivals:
                pkt.state = PacketState.EXPIRED
            return []

        # --- Determine the Fock mode mapping for this BS ---
        mappings = dest_comp.get_fock_mode_mapping()

        # Build a lookup: port_index → which sub-block and which mode (a/b)
        port_to_block: Dict[int, Tuple[int, str]] = {}
        for blk_idx, m in enumerate(mappings):
            port_to_block[m['a']] = (blk_idx, 'a')
            port_to_block[m['b']] = (blk_idx, 'b')

        # --- Group arriving packets by sub-block and Fock mode ---
        # block_photons[blk_idx][mode] = {photon_idx: (pkt, conn_info)}
        block_photons: Dict[int, Dict[str, Dict[int, Tuple]]] = {
            i: {'a': {}, 'b': {}} for i in range(len(mappings))
        }
        unmatched = []  # packets whose port doesn't fit a sub-block

        for pkt, conn_info, _ in arrivals:
            input_port = conn_info['dest_port_idx']
            if input_port in port_to_block:
                blk_idx, mode = port_to_block[input_port]
                block_photons[blk_idx][mode][pkt.photon_idx] = (pkt, conn_info)
            else:
                unmatched.append((pkt, conn_info))

        children: List[QuantumPacket] = []

        # --- Collect deduplicated outgoing connections per output port ---
        routing = graph['component_routing'].get(id(dest_comp), {})
        outgoing_by_port: Dict[int, List[int]] = {}
        seen: Set[int] = set()
        for out_list in routing.values():
            for out_idx in out_list:
                if out_idx in seen:
                    continue
                seen.add(out_idx)
                out_conn = graph['connections'][out_idx]
                sp = out_conn['source_port_idx']
                outgoing_by_port.setdefault(sp, []).append(out_idx)

        # --- Process each sub-block that has photons ---
        for blk_idx, modes in block_photons.items():
            n_a = len(modes['a'])  # photon count in Fock mode a
            n_b = len(modes['b'])  # photon count in Fock mode b
            total = n_a + n_b

            if total == 0:
                continue

            if total == 1:
                # Single photon — fall back to classical S-matrix split
                for mode_packets in (modes['a'], modes['b']):
                    for photon_idx, (pkt, conn_info) in mode_packets.items():
                        ch = self._split_packet(pkt, conn_info, family_id)
                        if ch:
                            children.extend(ch)
                        else:
                            pkt.state = PacketState.EXPIRED
                continue

            mapping = mappings[blk_idx]

            # Sample output photon numbers from exact quantum distribution
            p_out, q_out = dest_comp.fock_transform(n_a, n_b)
            # p_out photons exit via Fock mode c, q_out via Fock mode d

            # Collect all input packets (to expire them)
            all_input_pkts = []
            all_input_pkts.extend(modes['a'].values())
            all_input_pkts.extend(modes['b'].values())

            child_gen = max_gen + 1

            # Assign photon indices to outputs — reuse input photon_idxs
            input_photon_idxs = sorted(
                set(pkt.photon_idx for pkt, _ in all_input_pkts))

            # Distribute photon_idxs: first p_out go to mode c, rest to mode d
            c_photon_idxs = input_photon_idxs[:p_out]
            d_photon_idxs = input_photon_idxs[p_out:]

            # After Fock sampling the probabilistic choice is resolved —
            # each output photon is in a definite mode with unit amplitude.
            # (The S-matrix coefficients are already encoded in the Fock
            # distribution, so applying them again would double-count.)

            # Create child packets for mode c outputs
            c_port = mapping['c']
            for pidx in c_photon_idxs:
                for out_idx in outgoing_by_port.get(c_port, []):
                    out_conn = graph['connections'][out_idx]
                    child = self._make_packet(
                        family_id, out_idx, out_conn, 1.0+0j,
                        child_gen, photon_idx=pidx)
                    donor = modes['a'].get(pidx) or modes['b'].get(pidx)
                    if donor:
                        child.history_paths = list(donor[0].history_paths)
                    children.append(child)

            # Create child packets for mode d outputs
            d_port = mapping['d']
            for pidx in d_photon_idxs:
                for out_idx in outgoing_by_port.get(d_port, []):
                    out_conn = graph['connections'][out_idx]
                    child = self._make_packet(
                        family_id, out_idx, out_conn, 1.0+0j,
                        child_gen, photon_idx=pidx)
                    donor = modes['a'].get(pidx) or modes['b'].get(pidx)
                    if donor:
                        child.history_paths = list(donor[0].history_paths)
                    children.append(child)

            # Expire all input packets (they've been replaced)
            for pkt, _ in all_input_pkts:
                pkt.state = PacketState.EXPIRED

        # Handle unmatched packets with classical splitting
        for pkt, conn_info in unmatched:
            ch = self._split_packet(pkt, conn_info, family_id)
            if ch:
                children.extend(ch)
            else:
                pkt.state = PacketState.EXPIRED

        return children

    # ------------------------------------------------------------------
    # Detection
    # ------------------------------------------------------------------

    def _perform_detection(self, family: PacketFamily, now: float):
        """Probabilistic detection among arrived packets.

        For multi-photon families each photon (identified by ``photon_idx``)
        is resolved independently.  Coincidence statistics are recorded
        when more than one photon is detected per pulse.
        """
        arrived = [p for p in family.packets if p.state == PacketState.ARRIVED]
        if not arrived:
            family.fully_resolved = True
            return

        # ---- Group arrived packets by photon_idx ----
        by_photon: Dict[int, List[QuantumPacket]] = {}
        for pkt in arrived:
            by_photon.setdefault(pkt.photon_idx, []).append(pkt)

        chosen_detectors: List[object] = []  # one entry per photon

        for photon_idx in sorted(by_photon):
            pkts = by_photon[photon_idx]

            # Sum amplitudes coherently per detector for this photon
            det_amps: Dict[object, complex] = {}
            for pkt in pkts:
                det_amps.setdefault(pkt.detector, 0j)
                det_amps[pkt.detector] += pkt.amplitude

            probs = {det: abs(a) ** 2 for det, a in det_amps.items()}
            total_prob = sum(probs.values())

            if total_prob < 1e-10:
                for pkt in pkts:
                    pkt.state = PacketState.EXPIRED
                continue

            # Normalize
            for det in probs:
                probs[det] /= total_prob

            # Random draw
            r = random.random()
            cumulative = 0.0
            chosen = None
            for det, p in probs.items():
                cumulative += p
                if r <= cumulative:
                    chosen = det
                    break
            if chosen is None:
                chosen = list(probs.keys())[-1]

            chosen_detectors.append(chosen)

            # Mark packets for this photon
            for pkt in pkts:
                if pkt.detector == chosen:
                    pkt.state = PacketState.DETECTED
                    pkt.detection_time = now
                else:
                    pkt.state = PacketState.COLLAPSED
                    pkt.detection_time = now

        # ---- Update family state ----
        family.detected = True
        family.detected_detectors = chosen_detectors
        family.detected_detector = chosen_detectors[0] if chosen_detectors else None
        family.detection_time = now
        family.collapsed_time = now

        # ---- Update per-detector histogram ----
        for det in chosen_detectors:
            self._detection_counts[det] = self._detection_counts.get(det, 0) + 1
        self._total_detections += len(chosen_detectors)

        # ---- Update coincidence histogram ----
        self._total_pulses += 1
        if len(chosen_detectors) >= 2:
            key = frozenset(chosen_detectors)
            self._coincidence_counts[key] = self._coincidence_counts.get(key, 0) + 1

        # ---- Update PNR histogram ----
        photons_per_det: Dict[object, int] = {}
        for det in chosen_detectors:
            photons_per_det[det] = photons_per_det.get(det, 0) + 1
        for det, n in photons_per_det.items():
            if det not in self._pnr_counts:
                self._pnr_counts[det] = {}
            self._pnr_counts[det][n] = self._pnr_counts[det].get(n, 0) + 1

        # ---- Notify ----
        notified: Set = set()
        for det in chosen_detectors:
            if det not in notified and self.on_detection:
                self.on_detection(det)
                notified.add(det)

    # ------------------------------------------------------------------
    # Graph building
    # ------------------------------------------------------------------

    def _build_graph(self, wave_engine) -> Optional[Dict]:
        """Build a traversal graph from the wave optics engine's solved network."""
        if not hasattr(wave_engine, 'connections') or not wave_engine.connections:
            return None

        connections = []
        laser_conns = []
        detector_conns = []
        component_routing = {}  # id(component) -> {input_conn_idx -> [output_conn_indices]}

        for idx, conn in enumerate(wave_engine.connections):
            beam_id = f"beam_{idx}"
            amplitude = wave_engine.beam_amplitudes.get(beam_id, 0j)

            info = {
                'index': idx,
                'path': list(conn.path),
                'length': conn.length,
                'amplitude': amplitude,
                'phase_shift': conn.phase_shift,
                'source_component': conn.port1.component,
                'source_port_idx': conn.port1.port_index,
                'dest_component': conn.port2.component,
                'dest_port_idx': conn.port2.port_index,
            }
            connections.append(info)

            if conn.port1.component.component_type == 'laser':
                emission_port = getattr(conn.port1.component, 'EMISSION_PORT',
                                        conn.port1.port_index)
                if conn.port1.port_index == emission_port:
                    laser_conns.append(idx)
            if conn.port2.component.component_type == 'detector':
                detector_conns.append(idx)

        # Build routing table
        for idx, conn in enumerate(wave_engine.connections):
            dest = conn.port2.component
            if dest.component_type == 'detector':
                continue
            comp_id = id(dest)
            if comp_id not in component_routing:
                component_routing[comp_id] = {}

            # Find outgoing connections from dest
            outgoing = []
            for out_idx, out_conn in enumerate(wave_engine.connections):
                if out_conn.port1.component is dest:
                    outgoing.append(out_idx)

            component_routing[comp_id][idx] = outgoing

        return {
            'connections': connections,
            'laser_connections': laser_conns,
            'detector_connections': detector_conns,
            'component_routing': component_routing,
        }

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def _cleanup(self, now: float):
        """Remove fully resolved families that have finished animating."""
        self.families = [f for f in self.families
                         if not f.fully_resolved or (now - f.collapsed_time) < self.collapse_duration + 0.5]
