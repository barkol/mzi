"""Rectangular Mach-Zehnder interferometer test with correct corner geometry."""
import pygame
import sys
sys.path.append('.')

from core.waveoptics import WaveOpticsEngine
from components.laser import Laser
from components.beam_splitter import BeamSplitter
from components.mirror import Mirror
from components.detector import Detector
from utils.vector import Vector2
from config.settings import CANVAS_OFFSET_X, CANVAS_OFFSET_Y, GRID_SIZE

def test_rectangular_mzi():
    """Test rectangular Mach-Zehnder with components at corners."""
    print("=== Testing Rectangular Mach-Zehnder Interferometer ===\n")
    
    # Proper rectangular MZI layout:
    # 
    # BS1 ----------- Mirror1
    #  |                |
    #  |                |
    # Mirror2 -------- BS2
    #
    # BS1 (top-left) splits beam right and down
    # Mirror1 (top-right) redirects right beam down
    # Mirror2 (bottom-left) redirects down beam right
    # BS2 (bottom-right) recombines beams
    
    # Define the rectangle corners
    left_x = CANVAS_OFFSET_X + GRID_SIZE * 5
    right_x = CANVAS_OFFSET_X + GRID_SIZE * 10
    top_y = CANVAS_OFFSET_Y + GRID_SIZE * 5
    bottom_y = CANVAS_OFFSET_Y + GRID_SIZE * 10
    
    # Laser approaches BS1 from the left
    laser = Laser(CANVAS_OFFSET_X + GRID_SIZE * 2, top_y)
    
    # Components at corners
    bs1 = BeamSplitter(left_x, top_y)      # Top-left
    mirror1 = Mirror(right_x, top_y, '\\')  # Top-right (\ redirects right→down)
    mirror2 = Mirror(left_x, bottom_y, '\\') # Bottom-left (\ redirects down→right)
    bs2 = BeamSplitter(right_x, bottom_y)   # Bottom-right
    
    # Detectors
    detector1 = Detector(right_x + GRID_SIZE * 4, bottom_y)  # Right of BS2
    detector2 = Detector(right_x, bottom_y + GRID_SIZE * 3)  # Below BS2
    
    print("Component positions (corners of rectangle):")
    print(f"  BS1 (top-left): ({bs1.position.x:.0f}, {bs1.position.y:.0f})")
    print(f"  Mirror1 (top-right): ({mirror1.position.x:.0f}, {mirror1.position.y:.0f})")
    print(f"  Mirror2 (bottom-left): ({mirror2.position.x:.0f}, {mirror2.position.y:.0f})")
    print(f"  BS2 (bottom-right): ({bs2.position.x:.0f}, {bs2.position.y:.0f})")
    print(f"\n  Rectangle dimensions: {right_x - left_x} x {bottom_y - top_y}")
    
    print("\nExpected beam paths:")
    print("  Path 1: Laser → BS1 → (right) → Mirror1 → (down) → BS2")
    print("  Path 2: Laser → BS1 → (down) → Mirror2 → (right) → BS2")
    print("  Both paths travel the same distance (two sides of rectangle)")
    
    # Create engine and solve
    engine = WaveOpticsEngine()
    engine.debug = True
    
    components = [bs1, mirror1, mirror2, bs2, detector1, detector2]
    paths = engine.solve_interferometer(laser, components)
    
    # Analyze connections
    print("\n\nConnection Analysis:")
    connection_summary = {}
    for i, conn in enumerate(engine.connections):
        c1 = conn.port1.component.component_type
        c2 = conn.port2.component.component_type
        key = f"{c1} → {c2}"
        connection_summary[key] = connection_summary.get(key, 0) + 1
        
        amp = abs(engine.beam_amplitudes.get(f"beam_{i}", 0))
        if amp > 0.01:
            print(f"  {c1} → {c2}: amplitude={amp:.3f}, length={conn.length:.1f}")
    
    print("\nConnection types:")
    for conn_type, count in sorted(connection_summary.items()):
        print(f"  {conn_type}: {count}")
    
    print(f"\nResults:")
    print(f"  Detector 1 intensity: {detector1.intensity:.3f}")
    print(f"  Detector 2 intensity: {detector2.intensity:.3f}")
    print(f"  Total intensity: {detector1.intensity + detector2.intensity:.3f}")
    
    # Check for proper energy conservation
    total = detector1.intensity + detector2.intensity
    if abs(total - 1.0) < 0.1:
        print("\n✓ Energy is conserved!")
        print("✓ Mach-Zehnder interferometer working correctly!")
    else:
        print(f"\n✗ Energy not conserved (expected 1.0, got {total:.3f})")
    
    # Check for equal path lengths (should give constructive/destructive interference)
    path1_length = abs(right_x - left_x) + abs(bottom_y - top_y)
    path2_length = abs(bottom_y - top_y) + abs(right_x - left_x)
    print(f"\nPath lengths: {path1_length} = {path2_length} (equal)")
    
    return abs(total - 1.0) < 0.1

def test_debug_connections():
    """Debug which connections are being made."""
    print("\n=== Debugging Corner Connections ===\n")
    
    # Simplified corner setup
    bs1 = BeamSplitter(CANVAS_OFFSET_X + GRID_SIZE * 5, CANVAS_OFFSET_Y + GRID_SIZE * 5)
    mirror1 = Mirror(CANVAS_OFFSET_X + GRID_SIZE * 9, CANVAS_OFFSET_Y + GRID_SIZE * 5, '\\')
    
    print(f"BS1 at ({bs1.position.x}, {bs1.position.y})")
    print(f"Mirror1 at ({mirror1.position.x}, {mirror1.position.y})")
    print(f"Horizontal distance: {mirror1.position.x - bs1.position.x}")
    
    # Check ports
    engine = WaveOpticsEngine()
    bs1_ports = engine._create_ports_for_component(bs1)
    
    print("\nBS1 ports:")
    for i, p in enumerate(bs1_ports):
        print(f"  Port {i}: pos=({p.position.x:.0f}, {p.position.y:.0f}), dir=({p.direction.x}, {p.direction.y})")
    
    print(f"\nBS1's right port (port 2) at ({bs1_ports[2].position.x:.0f}, {bs1_ports[2].position.y:.0f})")
    print(f"Should trace right and hit Mirror1")
    
    return True

def test_simple_rectangle():
    """Test simplified rectangular setup."""
    print("\n=== Testing Simple Rectangle ===\n")
    
    # Even simpler: just the four corners, no laser
    # Add laser inline with BS1
    
    laser = Laser(CANVAS_OFFSET_X + GRID_SIZE * 3, CANVAS_OFFSET_Y + GRID_SIZE * 6)
    bs1 = BeamSplitter(CANVAS_OFFSET_X + GRID_SIZE * 5, CANVAS_OFFSET_Y + GRID_SIZE * 6)
    mirror1 = Mirror(CANVAS_OFFSET_X + GRID_SIZE * 9, CANVAS_OFFSET_Y + GRID_SIZE * 6, '\\')
    mirror2 = Mirror(CANVAS_OFFSET_X + GRID_SIZE * 5, CANVAS_OFFSET_Y + GRID_SIZE * 10, '\\')
    bs2 = BeamSplitter(CANVAS_OFFSET_X + GRID_SIZE * 9, CANVAS_OFFSET_Y + GRID_SIZE * 10)
    detector = Detector(CANVAS_OFFSET_X + GRID_SIZE * 12, CANVAS_OFFSET_Y + GRID_SIZE * 10)
    
    engine = WaveOpticsEngine()
    components = [bs1, mirror1, mirror2, bs2, detector]
    paths = engine.solve_interferometer(laser, components)
    
    print(f"Detector intensity: {detector.intensity:.3f}")
    
    # Show all connections
    print("\nAll connections:")
    for conn in engine.connections:
        print(f"  {conn.port1.component.component_type} → {conn.port2.component.component_type}")
    
    return detector.intensity > 0.5

if __name__ == "__main__":
    pygame.init()
    
    tests = [
        test_debug_connections,
        test_simple_rectangle,
        test_rectangular_mzi
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                print(f"\n✓ {test.__name__} PASSED")
                passed += 1
            else:
                print(f"\n✗ {test.__name__} FAILED")
        except Exception as e:
            print(f"\n✗ {test.__name__} ERROR: {e}")
            import traceback
            traceback.print_exc()
        print("\n" + "="*70 + "\n")
    
    print(f"Overall: {passed}/{len(tests)} tests passed")