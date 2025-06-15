"""Diagnostic test for wave optics engine."""
import pygame
import sys
sys.path.append('.')

from core.waveoptics import WaveOpticsEngine
from components.laser import Laser
from components.beam_splitter import BeamSplitter
from components.detector import Detector
from config.settings import CANVAS_OFFSET_X, CANVAS_OFFSET_Y, GRID_SIZE

def test_simple_setup():
    """Test the simplest possible setup: laser -> detector."""
    print("=== WAVE OPTICS DIAGNOSTIC ===\n")
    
    # Create simple setup
    laser = Laser(CANVAS_OFFSET_X + GRID_SIZE * 2, CANVAS_OFFSET_Y + GRID_SIZE * 5)
    detector = Detector(CANVAS_OFFSET_X + GRID_SIZE * 6, CANVAS_OFFSET_Y + GRID_SIZE * 5)
    
    engine = WaveOpticsEngine()
    engine.debug = True  # Enable debug output
    
    print("Test 1: Direct laser -> detector")
    print(f"  Laser at: {laser.position}")
    print(f"  Detector at: {detector.position}")
    print(f"  Distance: {laser.position.distance_to(detector.position):.1f}")
    
    # Solve
    paths = engine.solve_interferometer(laser, [detector])
    
    print(f"\nResults:")
    print(f"  Connections made: {len(engine.connections)}")
    print(f"  Beam paths: {len(paths)}")
    print(f"  Detector intensity: {detector.intensity:.3f}")
    
    # Show connections
    if engine.connections:
        for i, conn in enumerate(engine.connections):
            print(f"  Connection {i}: {conn.port1.component.component_type} -> {conn.port2.component.component_type}")
            print(f"    Path length: {conn.length:.1f}")
            beam_id = f"beam_{i}"
            amp = engine.beam_amplitudes.get(beam_id, 0)
            print(f"    Amplitude: {abs(amp):.3f}")
    
    # Test 2: With beam splitter
    print("\n\nTest 2: Laser -> BeamSplitter -> Detector")
    bs = BeamSplitter(CANVAS_OFFSET_X + GRID_SIZE * 4, CANVAS_OFFSET_Y + GRID_SIZE * 5)
    
    engine2 = WaveOpticsEngine()
    engine2.debug = True
    
    paths2 = engine2.solve_interferometer(laser, [bs, detector])
    
    print(f"\nResults:")
    print(f"  Connections made: {len(engine2.connections)}")
    print(f"  Beam paths: {len(paths2)}")
    print(f"  Detector intensity: {detector.intensity:.3f}")
    
    # Return success indicator
    return len(paths) > 0

if __name__ == "__main__":
    pygame.init()
    
    try:
        success = test_simple_setup()
        if success:
            print("\n✓ Basic connectivity is working")
        else:
            print("\n✗ No beams detected - there's a problem with the engine")
    except Exception as e:
        print(f"\n✗ Error: {e}")
        import traceback
        traceback.print_exc()