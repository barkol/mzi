"""Test dynamic component addition/removal with wave optics."""
import pygame
import sys
sys.path.append('.')

from core.waveoptics import WaveOpticsEngine
from components.laser import Laser
from components.beam_splitter import BeamSplitter
from components.mirror import Mirror
from components.detector import Detector
from config.settings import CANVAS_OFFSET_X, CANVAS_OFFSET_Y, GRID_SIZE

def test_dynamic_components():
    """Test adding and removing components dynamically."""
    print("=== Testing Dynamic Component Updates ===\n")
    
    # Create initial setup
    laser = Laser(CANVAS_OFFSET_X + GRID_SIZE * 2, CANVAS_OFFSET_Y + GRID_SIZE * 5)
    detector = Detector(CANVAS_OFFSET_X + GRID_SIZE * 10, CANVAS_OFFSET_Y + GRID_SIZE * 5)
    
    engine = WaveOpticsEngine()
    engine.debug = False
    
    # Test 1: Basic setup
    print("Test 1: Laser -> Detector")
    components = [detector]
    paths = engine.solve_interferometer(laser, components)
    print(f"  Detector intensity: {detector.intensity:.3f}")
    assert detector.intensity > 0.9, "Detector should receive light"
    
    # Test 2: Add a beam splitter
    print("\nTest 2: Add beam splitter in the path")
    bs = BeamSplitter(CANVAS_OFFSET_X + GRID_SIZE * 6, CANVAS_OFFSET_Y + GRID_SIZE * 5)
    components = [bs, detector]
    paths = engine.solve_interferometer(laser, components)
    print(f"  Detector intensity: {detector.intensity:.3f}")
    assert detector.intensity < 0.6 and detector.intensity > 0.4, "Detector should receive ~50%"
    
    # Test 3: Add second detector
    print("\nTest 3: Add second detector")
    detector2 = Detector(CANVAS_OFFSET_X + GRID_SIZE * 6, CANVAS_OFFSET_Y + GRID_SIZE * 8)
    components = [bs, detector, detector2]
    paths = engine.solve_interferometer(laser, components)
    print(f"  Detector 1 intensity: {detector.intensity:.3f}")
    print(f"  Detector 2 intensity: {detector2.intensity:.3f}")
    print(f"  Total: {detector.intensity + detector2.intensity:.3f}")
    assert abs(detector.intensity + detector2.intensity - 1.0) < 0.1, "Energy should be conserved"
    
    # Test 4: Remove beam splitter
    print("\nTest 4: Remove beam splitter")
    components = [detector, detector2]
    paths = engine.solve_interferometer(laser, components)
    print(f"  Detector 1 intensity: {detector.intensity:.3f}")
    print(f"  Detector 2 intensity: {detector2.intensity:.3f}")
    # Now only detector1 should get light (direct path)
    assert detector.intensity > 0.9, "Detector 1 should get all light"
    assert detector2.intensity < 0.1, "Detector 2 should get no light"
    
    # Test 5: Build a simple interferometer dynamically
    print("\nTest 5: Build interferometer step by step")
    bs1 = BeamSplitter(CANVAS_OFFSET_X + GRID_SIZE * 4, CANVAS_OFFSET_Y + GRID_SIZE * 5)
    
    # Step 1: Just BS1
    components = [bs1]
    paths = engine.solve_interferometer(laser, components)
    print("  Step 1: Added BS1")
    
    # Step 2: Add mirrors
    mirror1 = Mirror(CANVAS_OFFSET_X + GRID_SIZE * 7, CANVAS_OFFSET_Y + GRID_SIZE * 2, '\\')
    mirror2 = Mirror(CANVAS_OFFSET_X + GRID_SIZE * 7, CANVAS_OFFSET_Y + GRID_SIZE * 8, '/')
    components = [bs1, mirror1, mirror2]
    paths = engine.solve_interferometer(laser, components)
    print("  Step 2: Added mirrors")
    
    # Step 3: Add second BS
    bs2 = BeamSplitter(CANVAS_OFFSET_X + GRID_SIZE * 10, CANVAS_OFFSET_Y + GRID_SIZE * 5)
    components = [bs1, mirror1, mirror2, bs2]
    paths = engine.solve_interferometer(laser, components)
    print("  Step 3: Added BS2")
    
    # Step 4: Add detector
    det_final = Detector(CANVAS_OFFSET_X + GRID_SIZE * 13, CANVAS_OFFSET_Y + GRID_SIZE * 5)
    components = [bs1, mirror1, mirror2, bs2, det_final]
    paths = engine.solve_interferometer(laser, components)
    print("  Step 4: Added final detector")
    print(f"  Final detector intensity: {det_final.intensity:.3f}")
    
    # Step 5: Remove one mirror to break interference
    print("\n  Step 5: Remove one mirror")
    components = [bs1, mirror1, bs2, det_final]  # Removed mirror2
    paths = engine.solve_interferometer(laser, components)
    print(f"  Detector intensity after removing mirror: {det_final.intensity:.3f}")
    
    print("\n✓ All dynamic component tests passed!")
    return True

def test_rapid_changes():
    """Test rapid component changes."""
    print("\n=== Testing Rapid Component Changes ===\n")
    
    laser = Laser(100, 100)
    engine = WaveOpticsEngine()
    
    # Rapidly add and remove components
    for i in range(5):
        print(f"Iteration {i+1}:")
        
        # Create random configuration
        components = []
        
        # Add some components
        if i % 2 == 0:
            components.append(BeamSplitter(200, 100))
        if i % 3 == 0:
            components.append(Mirror(300, 100, '/'))
        
        # Always have a detector
        detector = Detector(400, 100)
        components.append(detector)
        
        # Solve
        paths = engine.solve_interferometer(laser, components)
        print(f"  Components: {len(components)}, Detector intensity: {detector.intensity:.3f}")
    
    print("\n✓ Rapid changes handled correctly!")
    return True

if __name__ == "__main__":
    pygame.init()
    
    try:
        test_dynamic_components()
        test_rapid_changes()
        print("\n✓ All tests passed!")
    except AssertionError as e:
        print(f"\n✗ Test failed: {e}")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()