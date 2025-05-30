"""Test utilities for debugging interferometer physics."""
import math
import cmath
from utils.vector import Vector2

class TestUtilities:
    """Provides test functions for debugging physics and components."""
    
    @staticmethod
    def test_detector_interference(components):
        """Test interference at detector with two beams."""
        print("\n=== DETECTOR INTERFERENCE TEST ===")
        
        # Find a detector
        detector = None
        for comp in components:
            if comp.component_type == 'detector':
                detector = comp
                break
        
        if detector:
            print(f"Testing interference at detector {detector.position}")
            
            # Test different phase differences
            phase_diffs = [0, math.pi/4, math.pi/2, 3*math.pi/4, math.pi]
            
            print("\nTwo beams with equal amplitudes (1/√2 each):")
            print("Single beam intensity: (1/√2)² = 0.5")
            
            for phase_diff in phase_diffs:
                detector.reset_frame()
                
                # Create two beams with same amplitude
                beam1 = {
                    'amplitude': 1/math.sqrt(2),
                    'phase': 0,
                    'accumulated_phase': 0,
                    'total_path_length': 100
                }
                
                beam2 = {
                    'amplitude': 1/math.sqrt(2),
                    'phase': phase_diff,
                    'accumulated_phase': phase_diff,
                    'total_path_length': 100
                }
                
                # Add beams to detector
                detector.add_beam(beam1)
                detector.add_beam(beam2)
                detector.finalize_frame()
                
                # Calculate expected intensity
                E1 = beam1['amplitude'] * cmath.exp(1j * beam1['phase'])
                E2 = beam2['amplitude'] * cmath.exp(1j * beam2['phase'])
                E_total = E1 + E2
                expected_intensity = abs(E_total) ** 2
                
                print(f"\nPhase difference: {phase_diff*180/math.pi:.0f}°")
                print(f"  Expected intensity: {expected_intensity:.3f} = {expected_intensity*100:.0f}%")
                print(f"  Actual intensity: {detector.intensity:.3f} = {detector.intensity*100:.0f}%")
                print(f"  Match: {'YES ✓' if abs(detector.intensity - expected_intensity) < 0.001 else 'NO ✗'}")
            
            print("\nNote: With constructive interference (0° phase diff),")
            print("intensity = 2.0 = 200% (relative to single beam at 100%)")
            print("or 400% relative to each input beam's 50% contribution")
            
            # Additional test with unit amplitude beams
            print("\n--- Test with unit amplitude beams ---")
            detector.reset_frame()
            beam_unit1 = {
                'amplitude': 1.0,
                'phase': 0,
                'accumulated_phase': 0,
                'total_path_length': 100
            }
            beam_unit2 = {
                'amplitude': 1.0,
                'phase': 0,  # Constructive
                'accumulated_phase': 0,
                'total_path_length': 100
            }
            detector.add_beam(beam_unit1)
            detector.add_beam(beam_unit2)
            detector.finalize_frame()
            print(f"Two unit amplitude beams (constructive):")
            print(f"  Single beam intensity: 1.0 = 100%")
            print(f"  Total intensity: {detector.intensity:.1f} = {detector.intensity*100:.0f}%")
            print(f"  This is 4× the single beam intensity!")
        else:
            print("No detector found! Place a detector first.")
    
    @staticmethod
    def test_mirrors(components):
        """Test mirror reflections for both orientations."""
        print("\n=== MIRROR REFLECTION TEST ===")
        
        mirrors = [c for c in components if c.component_type == 'mirror']
        if not mirrors:
            print("No mirrors found! Place some mirrors first.")
            return
        
        for mirror in mirrors:
            print(f"\nTesting {mirror.mirror_type} mirror at {mirror.position}")
            
            # Test all 4 input directions
            test_beams = [
                {'name': 'left', 'dir': Vector2(1, 0), 'port': 'A'},
                {'name': 'bottom', 'dir': Vector2(0, -1), 'port': 'B'},
                {'name': 'right', 'dir': Vector2(-1, 0), 'port': 'C'},
                {'name': 'top', 'dir': Vector2(0, 1), 'port': 'D'}
            ]
            
            for test in test_beams:
                mirror.reset_frame()
                beam = {
                    'position': mirror.position - test['dir'] * 50,
                    'direction': test['dir'],
                    'amplitude': 1.0,
                    'phase': 0,
                    'accumulated_phase': 0,
                    'total_path_length': 0,
                    'source_type': 'laser'
                }
                mirror.add_beam(beam)
                outputs = mirror.finalize_frame()
                
                if outputs:
                    out = outputs[0]
                    out_dir = ''
                    out_port = ''
                    if out['direction'].x > 0.5:
                        out_dir = 'right'
                        out_port = 'C'
                    elif out['direction'].x < -0.5:
                        out_dir = 'left'
                        out_port = 'A'
                    elif out['direction'].y > 0.5:
                        out_dir = 'down'
                        out_port = 'B'
                    elif out['direction'].y < -0.5:
                        out_dir = 'up'
                        out_port = 'D'
                    
                    print(f"  {test['name']} ({test['port']}) → {out_dir} ({out_port})")
                    
                    # Verify phase shift
                    phase_shift = out['phase'] - beam['phase']
                    print(f"    Phase shift: {phase_shift*180/math.pi:.0f}° (should be ±180°)")
            
            # Show expected behavior
            if mirror.mirror_type == '/':
                print("  Expected for '/' mirror: left↔top, bottom↔right")
            else:
                print("  Expected for '\\' mirror: left↔bottom, top↔right")
    
    @staticmethod
    def test_beam_splitter(components):
        """Test beam splitter with beams from all 4 directions."""
        print("\n=== BEAM SPLITTER TEST MODE ===")
        for comp in components:
            if comp.component_type == 'beamsplitter':
                print(f"\nTesting beam splitter at {comp.position}")
                print("Expected behavior for '\\' orientation:")
                print("  A (left) → C (right) transmitted, B (down) reflected")
                print("  B (bottom) → D (up) transmitted, A (left) reflected")
                print("  C (right) → A (left) transmitted, D (up) reflected")
                print("  D (top) → B (down) transmitted, C (right) reflected")
                
                comp.reset_frame()
                
                # Test all 4 input directions (corrected for screen coordinates)
                test_beams = [
                    {'name': 'A (from left, traveling RIGHT)', 'dir': Vector2(1, 0)},
                    {'name': 'B (from bottom, traveling UP)', 'dir': Vector2(0, -1)},
                    {'name': 'C (from right, traveling LEFT)', 'dir': Vector2(-1, 0)},
                    {'name': 'D (from top, traveling DOWN)', 'dir': Vector2(0, 1)}
                ]
                
                for test in test_beams:
                    print(f"\n  Test {test['name']}:")
                    comp.reset_frame()
                    test_beam = {
                        'position': comp.position - test['dir'] * 50,
                        'direction': test['dir'],
                        'amplitude': 1.0,
                        'phase': 0,
                        'accumulated_phase': 0,
                        'path_length': 0,
                        'total_path_length': 0,
                        'source_type': 'laser'
                    }
                    comp.add_beam(test_beam)
                    outputs = comp.finalize_frame()
                    
                    # Calculate total output power
                    total_out_power = sum(out['amplitude']**2 for out in outputs)
                    print(f"    Input power: 1.000")
                    print(f"    Outputs: {len(outputs)} beams")
                    
                    # Show each output beam
                    output_by_port = {'A': 0, 'B': 0, 'C': 0, 'D': 0}
                    for out in outputs:
                        dir_name = ''
                        port_name = ''
                        if out['direction'].x > 0.5:
                            dir_name = 'RIGHT'
                            port_name = 'C'
                        elif out['direction'].x < -0.5:
                            dir_name = 'LEFT'
                            port_name = 'A'
                        elif out['direction'].y > 0.5:
                            dir_name = 'DOWN'
                            port_name = 'B'
                        elif out['direction'].y < -0.5:
                            dir_name = 'UP'
                            port_name = 'D'
                        
                        output_by_port[port_name] = out['amplitude']**2
                        print(f"      Port {port_name} ({dir_name}): amp={out['amplitude']:.3f}, power={out['amplitude']**2:.3f}")
                    
                    # Check if any expected outputs are missing
                    print(f"    Total output power: {total_out_power:.3f}")
                    print(f"    Energy conserved: {'YES ✓' if abs(total_out_power - 1.0) < 0.001 else 'NO ✗'}")
                    
                    if abs(total_out_power - 1.0) > 0.001:
                        print(f"    ERROR: Power deviation = {(total_out_power - 1.0)*100:.1f}%")
                        
                        # Additional debugging for energy non-conservation
                        if hasattr(comp, 'get_info'):
                            info = comp.get_info()
                            print(f"    Component info: t={info['t']:.3f}, r={info['r']:.3f}, r'={info['r_prime']:.3f}")
                            if info['last_input'] is not None and info['last_output'] is not None:
                                print(f"    Last v_in: {info['last_input']}")
                                print(f"    Last v_out: {info['last_output']}")
                
                return
        
        print("No beam splitter found to test")
    
    @staticmethod
    def test_multiple_inputs(components):
        """Test multiple inputs to beam splitter."""
        print("\n=== MULTIPLE INPUT PORT TEST ===")
        for comp in components:
            if comp.component_type == 'beamsplitter':
                print(f"Testing beam splitter at {comp.position} with multiple inputs")
                
                # Test case 1: Inputs from A and C (opposite sides)
                print("\n--- Test 1: Inputs from A (left) and C (right) ---")
                comp.reset_frame()
                
                beam_A = {
                    'position': comp.position + Vector2(-50, 0),
                    'direction': Vector2(1, 0),  # Right
                    'amplitude': 1.0,
                    'phase': 0,
                    'accumulated_phase': 0,
                    'total_path_length': 100,
                    'source_type': 'laser'
                }
                
                beam_C = {
                    'position': comp.position + Vector2(50, 0),
                    'direction': Vector2(-1, 0),  # Left
                    'amplitude': 1.0,
                    'phase': 0,
                    'accumulated_phase': 0,
                    'total_path_length': 100,
                    'source_type': 'laser'
                }
                
                comp.add_beam(beam_A)
                comp.add_beam(beam_C)
                outputs = comp.finalize_frame()
                
                print("Inputs: A (left, amp=1.0), C (right, amp=1.0)")
                print("Expected outputs:")
                print("  Port A: C transmitted = 1/√2")
                print("  Port B: A reflected = i/√2")
                print("  Port C: A transmitted = 1/√2")
                print("  Port D: C reflected = i/√2")
                print("Actual outputs:")
                for out in outputs:
                    dir_name = ''
                    if out['direction'].x > 0.5: dir_name = 'C (RIGHT)'
                    elif out['direction'].x < -0.5: dir_name = 'A (LEFT)'
                    elif out['direction'].y > 0.5: dir_name = 'B (DOWN)'
                    elif out['direction'].y < -0.5: dir_name = 'D (UP)'
                    print(f"  {dir_name}: amp={out['amplitude']:.3f}, phase={out['phase']*180/math.pi:.1f}°")
                
                # Test case 2: All four inputs
                print("\n--- Test 2: Inputs from all four ports ---")
                comp.reset_frame()
                
                beams = [
                    {'pos': Vector2(-50, 0), 'dir': Vector2(1, 0), 'port': 'A'},
                    {'pos': Vector2(0, 50), 'dir': Vector2(0, -1), 'port': 'B'},
                    {'pos': Vector2(50, 0), 'dir': Vector2(-1, 0), 'port': 'C'},
                    {'pos': Vector2(0, -50), 'dir': Vector2(0, 1), 'port': 'D'}
                ]
                
                for beam_info in beams:
                    beam = {
                        'position': comp.position + beam_info['pos'],
                        'direction': beam_info['dir'],
                        'amplitude': 0.5,
                        'phase': 0,
                        'accumulated_phase': 0,
                        'total_path_length': 100,
                        'source_type': 'laser'
                    }
                    comp.add_beam(beam)
                
                outputs = comp.finalize_frame()
                
                print("Inputs: All ports with amp=0.5 each")
                print("Expected outputs (each port receives from two inputs):")
                print("  Port A: C transmitted + B reflected = 0.5/√2 + i*0.5/√2")
                print("  Port B: A reflected + D transmitted = i*0.5/√2 + 0.5/√2")
                print("  Port C: A transmitted + D reflected = 0.5/√2 + i*0.5/√2")
                print("  Port D: B transmitted + C reflected = 0.5/√2 + i*0.5/√2")
                print("Actual outputs:")
                total_out_power = 0
                for out in outputs:
                    dir_name = ''
                    if out['direction'].x > 0.5: dir_name = 'C (RIGHT)'
                    elif out['direction'].x < -0.5: dir_name = 'A (LEFT)'
                    elif out['direction'].y > 0.5: dir_name = 'B (DOWN)'
                    elif out['direction'].y < -0.5: dir_name = 'D (UP)'
                    power = out['amplitude']**2
                    total_out_power += power
                    print(f"  {dir_name}: amp={out['amplitude']:.3f}, phase={out['phase']*180/math.pi:.1f}°, power={power:.3f}")
                
                input_power = 4 * 0.5**2  # 4 inputs each with amplitude 0.5
                print(f"\nEnergy conservation check:")
                print(f"  Total input power: {input_power:.3f}")
                print(f"  Total output power: {total_out_power:.3f}")
                print(f"  Conserved: {'YES ✓' if abs(total_out_power - input_power) < 0.001 else 'NO ✗'}")
                
                # Test case 3: Interference within the beam splitter
                print("\n--- Test 3: Internal interference (A and B with phase difference) ---")
                comp.reset_frame()
                
                beam_A = {
                    'position': comp.position + Vector2(-50, 0),
                    'direction': Vector2(1, 0),
                    'amplitude': 1/math.sqrt(2),
                    'phase': 0,
                    'accumulated_phase': 0,
                    'total_path_length': 100,
                    'source_type': 'laser'
                }
                
                beam_B = {
                    'position': comp.position + Vector2(0, 50),
                    'direction': Vector2(0, -1),
                    'amplitude': 1/math.sqrt(2),
                    'phase': math.pi,  # 180° phase difference
                    'accumulated_phase': math.pi,
                    'total_path_length': 100,
                    'source_type': 'laser'
                }
                
                comp.add_beam(beam_A)
                comp.add_beam(beam_B)
                outputs = comp.finalize_frame()
                
                print("Inputs: A (amp=1/√2, phase=0°), B (amp=1/√2, phase=180°)")
                print("Expected interference at output A:")
                print("  From B reflected: i*(1/√2)*e^(iπ) / √2 = -i/2")
                print("  Total at A: -i/2 (only from B)")
                print("Actual outputs:")
                for out in outputs:
                    dir_name = ''
                    if out['direction'].x > 0.5: dir_name = 'C (RIGHT)'
                    elif out['direction'].x < -0.5: dir_name = 'A (LEFT)'
                    elif out['direction'].y > 0.5: dir_name = 'B (DOWN)'
                    elif out['direction'].y < -0.5: dir_name = 'D (UP)'
                    print(f"  {dir_name}: amp={out['amplitude']:.3f}, phase={out['phase']*180/math.pi:.1f}°")
                
                return
        
        print("No beam splitter found to test")
