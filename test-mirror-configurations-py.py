"""Comprehensive test for mirror configurations in wave optics engine."""
import pygame
import sys
import itertools
sys.path.append('.')

from core.waveoptics import WaveOpticsEngine
from components.laser import Laser
from components.mirror import Mirror
from components.detector import Detector
from config.settings import CANVAS_OFFSET_X, CANVAS_OFFSET_Y, GRID_SIZE
from utils.vector import Vector2

def grid_to_screen(grid_x, grid_y):
    """Convert grid coordinates to screen coordinates (centered in cell)."""
    screen_x = CANVAS_OFFSET_X + grid_x * GRID_SIZE + GRID_SIZE // 2
    screen_y = CANVAS_OFFSET_Y + grid_y * GRID_SIZE + GRID_SIZE // 2
    return screen_x, screen_y

def test_single_mirror():
    """Test single mirror reflections in all directions."""
    print("=== SINGLE MIRROR TEST ===\n")
    
    engine = WaveOpticsEngine()
    engine.debug = False
    
    # Test configurations: (laser_pos, mirror_pos, mirror_type, detector_pos, expected_direction)
    test_cases = [
        # '/' mirror tests
        ((2, 5), (5, 5), '/', (5, 2), "Beam right → '/' mirror → up"),
        ((5, 8), (5, 5), '/', (2, 5), "Beam up → '/' mirror → left"),
        ((8, 5), (5, 5), '/', (5, 8), "Beam left → '/' mirror → down"),
        ((5, 2), (5, 5), '/', (8, 5), "Beam down → '/' mirror → right"),
        
        # '\' mirror tests  
        ((2, 5), (5, 5), '\\', (5, 8), "Beam right → '\\' mirror → down"),
        ((5, 8), (5, 5), '\\', (8, 5), "Beam up → '\\' mirror → right"),
        ((8, 5), (5, 5), '\\', (5, 2), "Beam left → '\\' mirror → up"),
        ((5, 2), (5, 5), '\\', (2, 5), "Beam down → '\\' mirror → left"),
    ]
    
    all_passed = True
    
    for laser_grid, mirror_grid, mirror_type, detector_grid, description in test_cases:
        # Create components
        laser = Laser(*grid_to_screen(*laser_grid))
        mirror = Mirror(*grid_to_screen(*mirror_grid), mirror_type)
        detector = Detector(*grid_to_screen(*detector_grid))
        
        # Solve
        paths = engine.solve_interferometer(laser, [mirror, detector])
        
        # Check result
        expected_intensity = 1.0  # Perfect mirror should preserve all energy
        tolerance = 0.01
        
        passed = abs(detector.intensity - expected_intensity) < tolerance
        status = "✓ PASS" if passed else "✗ FAIL"
        
        print(f"{status}: {description}")
        print(f"  Detector intensity: {detector.intensity:.3f} (expected: {expected_intensity:.3f})")
        
        if not passed:
            all_passed = False
            print(f"  ERROR: Intensity mismatch! Difference: {abs(detector.intensity - expected_intensity):.3f}")
            
            # Debug info
            if len(paths) == 0:
                print("  WARNING: No beam paths found!")
            else:
                print(f"  Number of paths: {len(paths)}")
                for i, path in enumerate(paths):
                    print(f"    Path {i}: {len(path['path'])} points, amplitude={path['amplitude']:.3f}")
        
        print()
    
    return all_passed

def test_three_mirror_path():
    """Test beam path through 3 mirrors."""
    print("=== THREE MIRROR PATH TEST ===\n")
    
    engine = WaveOpticsEngine()
    engine.debug = False
    
    # Create a square path with 3 mirrors
    test_configurations = [
        # Configuration 1: Clockwise square
        {
            'name': 'Clockwise Square',
            'laser': (2, 5),
            'mirrors': [
                ((5, 5), '/'),   # Right → Up
                ((5, 2), '\\'),  # Up → Right  
                ((8, 2), '/'),   # Right → Down
            ],
            'detector': (8, 5)
        },
        # Configuration 2: Counter-clockwise square
        {
            'name': 'Counter-clockwise Square',
            'laser': (2, 5),
            'mirrors': [
                ((5, 5), '\\'),  # Right → Down
                ((5, 8), '/'),   # Down → Right
                ((8, 8), '\\'),  # Right → Up
            ],
            'detector': (8, 5)
        },
        # Configuration 3: Zig-zag path
        {
            'name': 'Zig-zag Path',
            'laser': (2, 2),
            'mirrors': [
                ((5, 2), '\\'),  # Right → Down
                ((5, 5), '/'),   # Down → Right
                ((8, 5), '\\'),  # Right → Down
            ],
            'detector': (8, 8)
        },
        # Configuration 4: All same type
        {
            'name': 'All Forward Slash',
            'laser': (2, 8),
            'mirrors': [
                ((5, 8), '/'),   # Right → Up
                ((5, 5), '/'),   # Up → Left
                ((2, 5), '/'),   # Left → Down
            ],
            'detector': (2, 8)
        },
    ]
    
    all_passed = True
    
    for config in test_configurations:
        print(f"Testing: {config['name']}")
        
        # Create components
        laser = Laser(*grid_to_screen(*config['laser']))
        mirrors = [Mirror(*grid_to_screen(*pos), mtype) for pos, mtype in config['mirrors']]
        detector = Detector(*grid_to_screen(*config['detector']))
        
        components = mirrors + [detector]
        
        # Solve
        paths = engine.solve_interferometer(laser, components)
        
        # Expected intensity after 3 perfect mirrors
        expected_intensity = 1.0  # No losses
        tolerance = 0.01
        
        passed = abs(detector.intensity - expected_intensity) < tolerance
        status = "✓ PASS" if passed else "✗ FAIL"
        
        print(f"  {status}: Detector intensity = {detector.intensity:.3f} (expected: {expected_intensity:.3f})")
        
        if not passed:
            all_passed = False
            print(f"  ERROR: Expected {expected_intensity:.3f} but got {detector.intensity:.3f}")
            
            # Detailed debug
            print(f"  Beam paths found: {len(paths)}")
            if len(paths) > 0:
                print("  Path details:")
                for i, path in enumerate(paths):
                    print(f"    Path {i}: amplitude={path['amplitude']:.3f}, phase={path['phase']:.3f}")
                    print(f"      Points: {len(path['path'])}")
                    if len(path['path']) > 0:
                        print(f"      Start: {path['path'][0]}")
                        print(f"      End: {path['path'][-1]}")
        
        # Show the path
        print(f"  Path: Laser{config['laser']} ", end='')
        for i, (pos, mtype) in enumerate(config['mirrors']):
            print(f"→ {mtype}{pos} ", end='')
        print(f"→ Detector{config['detector']}")
        print()
    
    return all_passed

def test_all_mirror_permutations():
    """Test all possible permutations of 3 mirrors."""
    print("=== ALL MIRROR PERMUTATIONS TEST ===\n")
    
    engine = WaveOpticsEngine()
    engine.debug = False
    
    # Fixed positions
    laser_pos = (2, 5)
    mirror_positions = [(5, 5), (8, 5), (8, 2)]
    detector_pos = (5, 2)
    
    # Generate all permutations of mirror types
    mirror_types = ['/', '\\']
    all_combinations = list(itertools.product(mirror_types, repeat=3))
    
    print(f"Testing {len(all_combinations)} mirror combinations...")
    
    results = []
    
    for combo in all_combinations:
        # Create components
        laser = Laser(*grid_to_screen(*laser_pos))
        mirrors = [Mirror(*grid_to_screen(*pos), mtype) 
                  for pos, mtype in zip(mirror_positions, combo)]
        detector = Detector(*grid_to_screen(*detector_pos))
        
        components = mirrors + [detector]
        
        # Solve
        paths = engine.solve_interferometer(laser, components)
        
        # Store result
        results.append({
            'combo': combo,
            'intensity': detector.intensity,
            'num_paths': len(paths)
        })
    
    # Analyze results
    print("\nResults Summary:")
    print("Combination | Intensity | Paths | Status")
    print("-" * 45)
    
    successful_combos = 0
    
    for result in results:
        combo_str = ''.join(result['combo'])
        intensity = result['intensity']
        num_paths = result['num_paths']
        
        # A successful path should have intensity close to 1.0
        is_successful = intensity > 0.9
        status = "✓" if is_successful else "✗"
        
        if is_successful:
            successful_combos += 1
        
        print(f"  {combo_str:^11} | {intensity:^9.3f} | {num_paths:^5} | {status}")
    
    print(f"\nSuccessful combinations: {successful_combos}/{len(all_combinations)}")
    
    # Find patterns
    print("\nAnalysis:")
    
    # Group by intensity
    intensity_groups = {}
    for result in results:
        intensity_key = f"{result['intensity']:.3f}"
        if intensity_key not in intensity_groups:
            intensity_groups[intensity_key] = []
        intensity_groups[intensity_key].append(result['combo'])
    
    print("\nGrouped by intensity:")
    for intensity, combos in sorted(intensity_groups.items(), key=lambda x: float(x[0]), reverse=True):
        print(f"  Intensity {intensity}: {len(combos)} combinations")
        if float(intensity) > 0.9:
            for combo in combos[:3]:  # Show first 3
                print(f"    {''.join(combo)}")
            if len(combos) > 3:
                print(f"    ... and {len(combos) - 3} more")
    
    return successful_combos > 0

def test_energy_conservation():
    """Test energy conservation with mirrors."""
    print("\n=== ENERGY CONSERVATION TEST ===\n")
    
    engine = WaveOpticsEngine()
    engine.debug = False
    
    # Test with increasing number of mirrors
    test_cases = [
        {
            'name': '1 Mirror',
            'laser': (2, 5),
            'mirrors': [((5, 5), '/')],
            'detector': (5, 2)
        },
        {
            'name': '2 Mirrors',
            'laser': (2, 5),
            'mirrors': [((5, 5), '/'), ((5, 2), '\\')],
            'detector': (8, 2)
        },
        {
            'name': '3 Mirrors',
            'laser': (2, 5),
            'mirrors': [((5, 5), '/'), ((5, 2), '\\'), ((8, 2), '/')],
            'detector': (8, 5)
        },
        {
            'name': '4 Mirrors (loop)',
            'laser': (2, 5),
            'mirrors': [((5, 5), '/'), ((5, 2), '\\'), ((8, 2), '/'), ((8, 5), '\\')],
            'detector': (5, 5)  # Back to start position
        }
    ]
    
    all_passed = True
    
    for test in test_cases:
        laser = Laser(*grid_to_screen(*test['laser']))
        mirrors = [Mirror(*grid_to_screen(*pos), mtype) for pos, mtype in test['mirrors']]
        detector = Detector(*grid_to_screen(*test['detector']))
        
        components = mirrors + [detector]
        
        # Solve
        paths = engine.solve_interferometer(laser, components)
        
        print(f"{test['name']}:")
        print(f"  Input power: 1.000")
        print(f"  Output power (detector): {detector.intensity:.3f}")
        print(f"  Energy conserved: {'YES' if abs(detector.intensity - 1.0) < 0.01 else 'NO'}")
        
        if abs(detector.intensity - 1.0) >= 0.01:
            all_passed = False
            print(f"  WARNING: Energy not conserved! Loss = {1.0 - detector.intensity:.3f}")
        
        print()
    
    return all_passed

def test_phase_accumulation():
    """Test phase accumulation through mirrors."""
    print("=== PHASE ACCUMULATION TEST ===\n")
    
    engine = WaveOpticsEngine()
    engine.debug = False
    
    # Each mirror should add π phase shift
    print("Testing phase shifts (each mirror adds π):")
    
    test_cases = [
        (0, "No mirrors"),
        (1, "1 mirror = π"),
        (2, "2 mirrors = 2π = 0"),
        (3, "3 mirrors = 3π = π"),
        (4, "4 mirrors = 4π = 0"),
    ]
    
    all_passed = True
    
    for num_mirrors, description in test_cases:
        # Create a straight line of mirrors
        laser = Laser(*grid_to_screen(2, 5))
        mirrors = []
        
        for i in range(num_mirrors):
            x = 4 + i * 2
            # Alternate mirror types to keep beam going right
            mirror_type = '\\' if i % 2 == 0 else '/'
            # Place mirrors in a zig-zag to keep beam moving right
            y = 5 + (1 if i % 2 == 0 else -1)
            mirrors.append(Mirror(*grid_to_screen(x, y), mirror_type))
        
        # Detector at the end
        detector_x = 4 + num_mirrors * 2
        detector_y = 5 + (0 if num_mirrors % 2 == 0 else 0)
        detector = Detector(*grid_to_screen(detector_x, detector_y))
        
        components = mirrors + [detector]
        
        # Solve
        paths = engine.solve_interferometer(laser, components)
        
        # Expected phase (in units of π)
        expected_phase_pi = num_mirrors % 2
        
        print(f"{description}:")
        print(f"  Detector intensity: {detector.intensity:.3f}")
        print(f"  Expected phase shift: {num_mirrors}π = {expected_phase_pi}π")
        
        # We can't directly measure phase from intensity with a single beam
        # But we can check that the beam arrives with correct amplitude
        if abs(detector.intensity - 1.0) >= 0.01:
            all_passed = False
            print(f"  WARNING: Unexpected intensity! Should be 1.0")
        
        print()
    
    return all_passed

def run_all_tests():
    """Run all mirror configuration tests."""
    print("="*60)
    print("MIRROR CONFIGURATION DIAGNOSTIC TESTS")
    print("="*60)
    print()
    
    pygame.init()
    
    # Run all test suites
    test_results = []
    
    print("\n" + "="*60 + "\n")
    result1 = test_single_mirror()
    test_results.append(("Single Mirror", result1))
    
    print("\n" + "="*60 + "\n")
    result2 = test_three_mirror_path()
    test_results.append(("Three Mirror Path", result2))
    
    print("\n" + "="*60 + "\n")
    result3 = test_all_mirror_permutations()
    test_results.append(("Mirror Permutations", result3))
    
    print("\n" + "="*60 + "\n")
    result4 = test_energy_conservation()
    test_results.append(("Energy Conservation", result4))
    
    print("\n" + "="*60 + "\n")
    result5 = test_phase_accumulation()
    test_results.append(("Phase Accumulation", result5))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    all_passed = True
    for test_name, passed in test_results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:.<40} {status}")
        if not passed:
            all_passed = False
    
    print("="*60)
    if all_passed:
        print("✓ ALL TESTS PASSED!")
    else:
        print("✗ SOME TESTS FAILED - Check mirror implementations")
    print("="*60)
    
    return all_passed

if __name__ == "__main__":
    try:
        success = run_all_tests()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)