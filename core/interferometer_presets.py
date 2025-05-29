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
        print("\n=== COMPLETE INTERFEROMETER TEST ===")
        print("This test simulates a full Mach-Zehnder interferometer")
        
        # Clear and setup ideal interferometer
        components.clear()
        
        # Place components in a standard MZ configuration
        # Remember: In pygame, Y increases DOWNWARD
        
        # Laser at left
        if laser:
            laser.position = Vector2(CANVAS_OFFSET_X + 2*GRID_SIZE, CANVAS_OFFSET_Y + 8*GRID_SIZE)
        
        # First beam splitter
        bs1 = BeamSplitter(CANVAS_OFFSET_X + 6*GRID_SIZE, CANVAS_OFFSET_Y + 8*GRID_SIZE)
        components.append(bs1)
        
        # Mirrors for upper path (smaller Y values in pygame)
        # First mirror: beam going UP needs to turn RIGHT
        mirror1 = Mirror(CANVAS_OFFSET_X + 6*GRID_SIZE, CANVAS_OFFSET_Y + 4*GRID_SIZE, '/')
        # Second mirror: beam going RIGHT needs to turn DOWN
        mirror2 = Mirror(CANVAS_OFFSET_X + 12*GRID_SIZE, CANVAS_OFFSET_Y + 4*GRID_SIZE, '\\')
        components.append(mirror1)
        components.append(mirror2)
        
        # Second beam splitter
        bs2 = BeamSplitter(CANVAS_OFFSET_X + 12*GRID_SIZE, CANVAS_OFFSET_Y + 8*GRID_SIZE)
        components.append(bs2)
        
        # Detectors
        det1 = Detector(CANVAS_OFFSET_X + 16*GRID_SIZE, CANVAS_OFFSET_Y + 8*GRID_SIZE)
        det2 = Detector(CANVAS_OFFSET_X + 12*GRID_SIZE, CANVAS_OFFSET_Y + 12*GRID_SIZE)
        components.append(det1)
        components.append(det2)
        
        print("Standard Mach-Zehnder interferometer created!")
        print("Upper path goes through two mirrors (Y=4 in grid)")
        print("Lower path goes straight through (Y=8 in grid)")
        print("Adjust phase slider to see interference!")
        
        # Calculate path difference
        # Upper path: up 4 units (diagonal), right 6 units, down 4 units (diagonal)
        upper_path = math.sqrt(2) * 4 * GRID_SIZE + 6 * GRID_SIZE + math.sqrt(2) * 4 * GRID_SIZE
        # Lower path: straight 6 grid units
        lower_path = 6 * GRID_SIZE
        path_diff = upper_path - lower_path
        print(f"\nPath difference: {path_diff:.1f}px = {path_diff/WAVELENGTH:.2f}λ")
        print(f"Upper path: {upper_path:.1f}px (includes two diagonal segments)")
        print(f"Lower path: {lower_path:.1f}px (straight through)")
    
    @staticmethod
    def create_asymmetric_mz(components, laser):
        """Create asymmetric Mach-Zehnder for better interference demo."""
        print("\n=== ASYMMETRIC MACH-ZEHNDER SETUP ===")
        print("Creating interferometer with deliberate path length difference")
        
        # Clear and setup
        components.clear()
        
        # Laser
        if laser:
            laser.position = Vector2(CANVAS_OFFSET_X + 2*GRID_SIZE, CANVAS_OFFSET_Y + 8*GRID_SIZE)
        
        # First beam splitter
        bs1 = BeamSplitter(CANVAS_OFFSET_X + 5*GRID_SIZE, CANVAS_OFFSET_Y + 8*GRID_SIZE)
        components.append(bs1)
        
        # Upper path - make it longer with more mirrors
        # First up
        m1 = Mirror(CANVAS_OFFSET_X + 5*GRID_SIZE, CANVAS_OFFSET_Y + 3*GRID_SIZE, '/')
        # Then right
        m2 = Mirror(CANVAS_OFFSET_X + 8*GRID_SIZE, CANVAS_OFFSET_Y + 3*GRID_SIZE, '\\')
        # Extra length - go further right
        m3 = Mirror(CANVAS_OFFSET_X + 14*GRID_SIZE, CANVAS_OFFSET_Y + 3*GRID_SIZE, '\\')
        # Then down
        m4 = Mirror(CANVAS_OFFSET_X + 14*GRID_SIZE, CANVAS_OFFSET_Y + 8*GRID_SIZE, '/')
        
        components.extend([m1, m2, m3, m4])
        
        # Second beam splitter
        bs2 = BeamSplitter(CANVAS_OFFSET_X + 11*GRID_SIZE, CANVAS_OFFSET_Y + 8*GRID_SIZE)
        components.append(bs2)
        
        # Detectors
        det1 = Detector(CANVAS_OFFSET_X + 15*GRID_SIZE, CANVAS_OFFSET_Y + 8*GRID_SIZE)
        det2 = Detector(CANVAS_OFFSET_X + 11*GRID_SIZE, CANVAS_OFFSET_Y + 12*GRID_SIZE)
        components.append(det1)
        components.append(det2)
        
        # Calculate paths
        # Upper: up 5, right 3, right 6, down 5 (all diagonal except middle)
        upper_diagonal = 2 * 5 * math.sqrt(2) * GRID_SIZE
        upper_straight = 9 * GRID_SIZE
        upper_total = upper_diagonal + upper_straight
        
        # Lower: straight 6 grid units
        lower_total = 6 * GRID_SIZE
        
        path_diff = upper_total - lower_total
        
        print(f"\nPath lengths:")
        print(f"  Upper path: {upper_total:.1f}px = {upper_total/WAVELENGTH:.2f}λ")
        print(f"  Lower path: {lower_total:.1f}px = {lower_total/WAVELENGTH:.2f}λ")
        print(f"  Path difference: {path_diff:.1f}px = {path_diff/WAVELENGTH:.2f}λ")
        print(f"\nThis gives a phase difference of {(path_diff/WAVELENGTH)*360:.1f}° from path alone")
        print("Plus any additional phase from the slider!")
    
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
        
        # Create a simple interferometer that feeds into the beam splitter from two ports
        # First beam splitter to split the laser
        bs1 = BeamSplitter(CANVAS_OFFSET_X + 4*GRID_SIZE, CANVAS_OFFSET_Y + 8*GRID_SIZE)
        components.append(bs1)
        
        # Upper path to port D (top) of central BS
        # Need beam to go UP then RIGHT then DOWN
        m1 = Mirror(CANVAS_OFFSET_X + 4*GRID_SIZE, CANVAS_OFFSET_Y + 4*GRID_SIZE, '/')  # UP to RIGHT
        m2 = Mirror(CANVAS_OFFSET_X + 10*GRID_SIZE, CANVAS_OFFSET_Y + 4*GRID_SIZE, '\\')  # RIGHT to DOWN
        components.extend([m1, m2])
        
        # Lower path - add delay to create phase difference
        # Extra mirrors to lengthen path before going to port A
        m3 = Mirror(CANVAS_OFFSET_X + 4*GRID_SIZE, CANVAS_OFFSET_Y + 12*GRID_SIZE, '/')  # DOWN to RIGHT
        m4 = Mirror(CANVAS_OFFSET_X + 7*GRID_SIZE, CANVAS_OFFSET_Y + 12*GRID_SIZE, '\\')  # RIGHT to UP
        m5 = Mirror(CANVAS_OFFSET_X + 7*GRID_SIZE, CANVAS_OFFSET_Y + 8*GRID_SIZE, '/')  # UP to RIGHT
        components.extend([m3, m4, m5])
        
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
        print("1. Laser is split by first BS into two paths")
        print("2. Upper path (shorter) enters central BS from TOP (port D)")
        print("3. Lower path (longer) enters central BS from LEFT (port A)")
        print("4. The two beams interfere inside the central BS")
        print("5. Output intensities depend on the phase difference!")
        print("\nExpected behavior:")
        print("- Port B output: Gets contributions from both inputs")
        print("- Port C output: Gets contributions from both inputs")
        print("- Ports A and D: Only get from one input each")
        print("\nAdjust phase slider to see interference in action!")
    
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