"""Pre-built interferometer configurations."""
import math
from components.beam_splitter import BeamSplitter
from components.mirror import Mirror
from components.detector import Detector
from utils.vector import Vector2
from config.settings import CANVAS_OFFSET_X, CANVAS_OFFSET_Y, GRID_SIZE, WAVELENGTH

class InterferometerPresets:
    """Provides pre-built interferometer configurations for testing and demos."""
    
    @staticmethod
    def create_mach_zehnder(components, laser):
        """Create a standard Mach-Zehnder interferometer."""
        print("\n=== COMPLETE MACH-ZEHNDER INTERFEROMETER ===")
        print("Creating a standard MZ configuration")
        
        # Clear and setup
        components.clear()
        
        # Laser at left
        if laser:
            laser.position = Vector2(CANVAS_OFFSET_X + 2*GRID_SIZE, CANVAS_OFFSET_Y + 8*GRID_SIZE)
        
        # First beam splitter
        bs1 = BeamSplitter(CANVAS_OFFSET_X + 6*GRID_SIZE, CANVAS_OFFSET_Y + 8*GRID_SIZE)
        components.append(bs1)
        
        # Upper arm: straight path (transmitted through BS1)
        # No mirrors needed - beam goes straight from BS1 to BS2
        
        # Lower arm: reflected path needs careful routing
        # At BS1: beam from left (A) is reflected down (B)
        # Need to route this around to enter BS2 from bottom
        
        # Mirror 1: Catch the downward beam and reflect it right
        m1 = Mirror(CANVAS_OFFSET_X + 6*GRID_SIZE, CANVAS_OFFSET_Y + 11*GRID_SIZE, '\\')
        # m1: down→right (beam from top reflects right)
        
        # Mirror 2: Reflect the rightward beam up to BS2
        m2 = Mirror(CANVAS_OFFSET_X + 12*GRID_SIZE, CANVAS_OFFSET_Y + 11*GRID_SIZE, '/')
        # m2: right→up (beam from left reflects up)
        
        components.extend([m1, m2])
        
        # Second beam splitter
        bs2 = BeamSplitter(CANVAS_OFFSET_X + 12*GRID_SIZE, CANVAS_OFFSET_Y + 8*GRID_SIZE)
        components.append(bs2)
        
        # Detectors
        # At BS2:
        # - Upper beam (from left A) → transmitted right (C) or reflected down (B)
        # - Lower beam (from bottom B) → transmitted up (D) or reflected left (A)
        det1 = Detector(CANVAS_OFFSET_X + 16*GRID_SIZE, CANVAS_OFFSET_Y + 8*GRID_SIZE)  # Right output
        det2 = Detector(CANVAS_OFFSET_X + 12*GRID_SIZE, CANVAS_OFFSET_Y + 12*GRID_SIZE)  # Bottom output
        components.append(det1)
        components.append(det2)
        
        print("\nMach-Zehnder interferometer created!")
        print("Upper arm: straight through (6 grid units)")
        print("Lower arm: down 3, right 6, up 3 (12 grid units)")
        
        # Calculate path difference
        upper_path = 6 * GRID_SIZE
        lower_path = 3 * GRID_SIZE + 6 * GRID_SIZE + 3 * GRID_SIZE
        path_diff = lower_path - upper_path
        
        print(f"\nPath difference: {path_diff:.1f}px = {path_diff/WAVELENGTH:.2f}λ")
        print("This creates a fixed phase difference based on path lengths")
        print("\nNote: Both beams interfere at BOTH detectors")
        print("- Right detector gets: upper (transmitted) + lower (reflected left then transmitted)")
        print("- Bottom detector gets: upper (reflected down) + lower (transmitted up then reflected)")
    
    @staticmethod
    def create_asymmetric_mz(components, laser):
        """Create asymmetric Mach-Zehnder for better interference demo."""
        print("\n=== ASYMMETRIC MACH-ZEHNDER SETUP ===")
        print("Creating interferometer with larger path length difference")
        
        # Clear and setup
        components.clear()
        
        # Laser
        if laser:
            laser.position = Vector2(CANVAS_OFFSET_X + 2*GRID_SIZE, CANVAS_OFFSET_Y + 8*GRID_SIZE)
        
        # First beam splitter
        bs1 = BeamSplitter(CANVAS_OFFSET_X + 5*GRID_SIZE, CANVAS_OFFSET_Y + 8*GRID_SIZE)
        components.append(bs1)
        
        # Upper arm: keep it simple and straight
        # Just the transmitted beam going straight through
        
        # Lower arm: make it much longer with a zigzag path
        # Beam is reflected down at BS1
        
        # First segment: down
        m1 = Mirror(CANVAS_OFFSET_X + 5*GRID_SIZE, CANVAS_OFFSET_Y + 13*GRID_SIZE, '\\')  # down→right
        
        # Zigzag to add length
        m2 = Mirror(CANVAS_OFFSET_X + 10*GRID_SIZE, CANVAS_OFFSET_Y + 13*GRID_SIZE, '/')  # right→up
        m3 = Mirror(CANVAS_OFFSET_X + 10*GRID_SIZE, CANVAS_OFFSET_Y + 10*GRID_SIZE, '\\')  # up→right
        
        # Route back to BS2
        m4 = Mirror(CANVAS_OFFSET_X + 14*GRID_SIZE, CANVAS_OFFSET_Y + 10*GRID_SIZE, '/')  # right→up
        
        components.extend([m1, m2, m3, m4])
        
        # Second beam splitter
        bs2 = BeamSplitter(CANVAS_OFFSET_X + 14*GRID_SIZE, CANVAS_OFFSET_Y + 8*GRID_SIZE)
        components.append(bs2)
        
        # Detectors
        det1 = Detector(CANVAS_OFFSET_X + 18*GRID_SIZE, CANVAS_OFFSET_Y + 8*GRID_SIZE)
        det2 = Detector(CANVAS_OFFSET_X + 14*GRID_SIZE, CANVAS_OFFSET_Y + 12*GRID_SIZE)
        components.append(det1)
        components.append(det2)
        
        # Calculate paths
        upper_path = 9 * GRID_SIZE  # Straight from BS1 to BS2
        lower_path = (5 * GRID_SIZE +    # Down to m1
                     5 * GRID_SIZE +     # Right to m2
                     3 * GRID_SIZE +     # Up to m3
                     4 * GRID_SIZE +     # Right to m4
                     2 * GRID_SIZE)      # Up to BS2
        
        path_diff = lower_path - upper_path
        
        print(f"\nPath lengths:")
        print(f"  Upper arm: {upper_path:.1f}px = {upper_path/WAVELENGTH:.2f}λ")
        print(f"  Lower arm: {lower_path:.1f}px = {lower_path/WAVELENGTH:.2f}λ")
        print(f"  Path difference: {path_diff:.1f}px = {path_diff/WAVELENGTH:.2f}λ")
        print(f"\nThis creates a phase difference of {(path_diff/WAVELENGTH)*360:.1f}° from path length alone")
    
    @staticmethod
    def create_beam_splitter_demo(components, laser):
        """Demo: Create setup showing internal beam splitter interference."""
        print("\n=== BEAM SPLITTER INTERFERENCE DEMO ===")
        
        # Clear existing setup
        components.clear()
        
        # Place central beam splitter
        central_bs = BeamSplitter(CANVAS_OFFSET_X + 10*GRID_SIZE, CANVAS_OFFSET_Y + 8*GRID_SIZE)
        central_bs.debug = True
        components.append(central_bs)
        
        # Create paths to feed beams into two different ports of central BS
        # First beam splitter to split the laser
        bs1 = BeamSplitter(CANVAS_OFFSET_X + 4*GRID_SIZE, CANVAS_OFFSET_Y + 8*GRID_SIZE)
        components.append(bs1)
        
        # Path 1: Transmitted beam goes straight to central BS (enters from left, port A)
        # No mirrors needed
        
        # Path 2: Reflected beam (goes down) needs to be routed to enter from different port
        # Let's route it to enter from top (port D)
        
        # Mirror to catch downward beam and send right
        m1 = Mirror(CANVAS_OFFSET_X + 4*GRID_SIZE, CANVAS_OFFSET_Y + 12*GRID_SIZE, '\\')  # down→right
        # Mirror to send beam up
        m2 = Mirror(CANVAS_OFFSET_X + 10*GRID_SIZE, CANVAS_OFFSET_Y + 12*GRID_SIZE, '/')  # right→up
        
        components.extend([m1, m2])
        
        # Add detectors at all outputs of central BS
        det_positions = [
            (central_bs.position.x - 80, central_bs.position.y, "A (LEFT)"),
            (central_bs.position.x, central_bs.position.y + 80, "B (DOWN)"),
            (central_bs.position.x + 80, central_bs.position.y, "C (RIGHT)"),
            (central_bs.position.x, central_bs.position.y - 80, "D (UP)")
        ]
        
        for x, y, label in det_positions:
            det = Detector(x, y)
            components.append(det)
            print(f"  Detector placed at output {label}")
        
        # Position laser
        if laser:
            laser.position = Vector2(CANVAS_OFFSET_X + GRID_SIZE, CANVAS_OFFSET_Y + 8*GRID_SIZE)
        
        print("\nThis setup demonstrates interference WITHIN a beam splitter:")
        print("1. Laser is split by first BS")
        print("2. Path 1 (transmitted): enters central BS from LEFT (port A)")
        print("3. Path 2 (reflected): enters central BS from TOP (port D)")
        print("4. The two beams interfere inside the central BS")
        print("\nAt the central BS:")
        print("- Beam from A: transmitted to C, reflected to B")
        print("- Beam from D: transmitted to B, reflected to C")
        print("- Both outputs (B and C) show interference!")
        print("- Outputs A and D are zero (no input from B or C)")
        print("\nThe interference pattern depends on the path length difference!")
    
    @staticmethod
    def add_visual_test_detectors(components):
        """Visual test: place detectors around beam splitter."""
        print("\n=== VISUAL DIRECTION TEST ===")
        for comp in components:
            if comp.component_type == 'beamsplitter':
                bs_pos = comp.position
                print(f"Placing detectors around beam splitter at {bs_pos}")
                
                # Place detectors at all 4 positions
                detector_positions = [
                    (bs_pos.x - 80, bs_pos.y, "LEFT (A)"),
                    (bs_pos.x, bs_pos.y + 80, "DOWN (B)"),
                    (bs_pos.x + 80, bs_pos.y, "RIGHT (C)"),
                    (bs_pos.x, bs_pos.y - 80, "UP (D)")
                ]
                
                added = []
                for x, y, label in detector_positions:
                    # Check if position is free
                    occupied = False
                    for existing in components:
                        if existing.position.distance_to(Vector2(x, y)) < GRID_SIZE:
                            occupied = True
                            break
                    
                    if not occupied:
                        det = Detector(x, y)
                        added.append(det)
                        print(f"  Placed detector at {label}")
                
                components.extend(added)
                print("Now test with laser from different directions to verify routing")
                break
