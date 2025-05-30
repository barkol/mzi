"""Keyboard command handler for debug and test functions."""
import pygame
import math
import cmath
from core.interferometer_presets import InterferometerPresets
from core.test_utilities import TestUtilities

class KeyboardHandler:
    """Handles keyboard shortcuts and debug commands."""
    
    def __init__(self, game):
        self.game = game
        self.presets = InterferometerPresets()
        self.tests = TestUtilities()
    
    def handle_key(self, event):
        """Handle keyboard event and return True if handled."""
        if event.type != pygame.KEYDOWN:
            return False
            
        # Basic toggles
        if event.key == pygame.K_o:
            self.game.show_opd_info = not self.game.show_opd_info
            print(f"OPD display: {'ON' if self.game.show_opd_info else 'OFF'}")
            return True
            
        elif event.key == pygame.K_g:
            # Toggle debug mode for all components
            new_debug_state = not self.game.laser.debug
            self.game.laser.debug = new_debug_state
            self.game.beam_tracer.debug = new_debug_state
            self.game.beam_renderer.set_debug(new_debug_state)
            self.game.component_manager.set_debug_mode(new_debug_state)
            print(f"\nDebug mode: {'ON' if new_debug_state else 'OFF'} for all components")
            return True
            
        # Preset interferometer setups
        elif event.key == pygame.K_c:
            # Complete Mach-Zehnder interferometer
            self.presets.create_mach_zehnder(self.game.component_manager.components, self.game.laser)
            return True
            
        elif event.key == pygame.K_a:
            # Asymmetric Mach-Zehnder
            self.presets.create_asymmetric_mz(self.game.component_manager.components, self.game.laser)
            return True
            
        elif event.key == pygame.K_d and pygame.key.get_mods() & pygame.KMOD_SHIFT:
            # Beam splitter interference demo (Shift+D)
            self.presets.create_beam_splitter_demo(self.game.component_manager.components, self.game.laser)
            return True
            
        # Test functions
        elif event.key == pygame.K_v:
            # Visual direction test
            self.presets.add_visual_test_detectors(self.game.component_manager.components)
            return True
            
        elif event.key == pygame.K_i:
            # Detector interference test
            self.tests.test_detector_interference(self.game.component_manager.components)
            return True
            
        elif event.key == pygame.K_t:
            # Beam splitter test
            self.tests.test_beam_splitter(self.game.component_manager.components)
            return True
            
        elif event.key == pygame.K_m:
            # Multiple input test
            self.tests.test_multiple_inputs(self.game.component_manager.components)
            return True
            
        elif event.key == pygame.K_r:
            # Test mirrors
            self.tests.test_mirrors(self.game.component_manager.components)
            return True
            
        elif event.key == pygame.K_h:
            # Show help
            self._show_help()
            return True
            
        return False
    
    def _show_help(self):
        """Show coordinate system help."""
        print("\n=== PYGAME COORDINATE SYSTEM ===")
        print("Important: Y-axis is INVERTED in pygame!")
        print("")
        print("Screen coordinates:")
        print("  (0,0) ────→ +X")
        print("    │")
        print("    ↓")
        print("   +Y")
        print("")
        print("This means:")
        print("- UP in physics = NEGATIVE Y in pygame")
        print("- DOWN in physics = POSITIVE Y in pygame")
        print("")
        print("Beam splitter behavior ('\\' orientation):")
        print("  Input from LEFT (A):")
        print("    - Transmitted RIGHT (C)")
        print("    - Reflected DOWN (B)")
        print("  Input from BOTTOM (B):")
        print("    - Transmitted UP (D)")
        print("    - Reflected LEFT (A)")
        print("")
        print("Mirror reflections in pygame coords:")
        print("  '/' mirror:")
        print("    - UP (-Y) → RIGHT (+X)")
        print("    - LEFT (-X) → DOWN (+Y)")
        print("  '\\' mirror:")
        print("    - UP (-Y) → LEFT (-X)")
        print("    - RIGHT (+X) → DOWN (+Y)")
        print("")
        print("Beam splitter ports (screen coordinates):")
        print("  Port D (top) = negative Y direction")
        print("  Port B (bottom) = positive Y direction")
        print("  Port A (left) = negative X direction")
        print("  Port C (right) = positive X direction")
        print("")
        print("Key bindings:")
        print("  G = Toggle debug mode for all components")
        print("  O = Toggle OPD display")
        print("  C = Create Mach-Zehnder interferometer")
        print("  A = Create asymmetric MZ interferometer")
        print("  Shift+D = Beam splitter interference demo")
        print("  V = Visual direction test (add detectors)")
        print("  I = Detector interference test")
        print("  T = Beam splitter direction test")
        print("  M = Multiple input port test")
        print("  R = Mirror reflection test")
        print("  H = Show this help")
