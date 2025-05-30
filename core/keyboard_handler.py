"""Keyboard command handler for debug and test functions."""
import pygame
import math
import cmath
from core.test_utilities import TestUtilities

class KeyboardHandler:
    """Handles keyboard shortcuts and debug commands."""
    
    def __init__(self, game):
        self.game = game
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
            
        elif event.key == pygame.K_l:
            # Toggle leaderboard display
            if self.game.leaderboard_display.visible:
                self.game.leaderboard_display.hide()
            else:
                self.game.leaderboard_display.show()
            return True
            
        elif event.key == pygame.K_g:
            # Toggle debug mode for all components
            new_debug_state = not self.game.laser.debug
            self.game.laser.debug = new_debug_state
            self.game.beam_tracer.debug = new_debug_state
            self.game.beam_renderer.set_debug(new_debug_state)
            self.game.component_manager.set_debug_mode(new_debug_state)
            print(f"\nDebug mode: {'ON' if new_debug_state else 'OFF'} for all components")
            self.game.right_panel.add_debug_message(f"Debug mode: {'ON' if new_debug_state else 'OFF'}")
            if new_debug_state:
                self.game.right_panel.add_debug_message("Switch to Debug view with Shift+H")
            return True
            
        # New session
        elif event.key == pygame.K_n and pygame.key.get_mods() & pygame.KMOD_SHIFT:
            # Shift+N - New session (reset score and completed challenges)
            self.game.score = 0
            self.game.controls.score = self.game.score
            self.game.completed_challenges.clear()
            self.game.component_manager.clear_all(self.game.laser)
            print("\n=== NEW SESSION STARTED ===")
            print("Score reset to initial value")
            print("All challenges can be completed again for points")
            self.game.controls.set_status("New session started!")
            
            # Load default challenge (Basic Mach-Zehnder)
            challenges = self.game.challenge_manager.get_challenge_list()
            if challenges:
                for name, title in challenges:
                    if name == "basic_mz":
                        self.game.challenge_manager.set_current_challenge(name)
                        self.game.controls.set_challenge(title)
                        self.game.right_panel.add_debug_message(f"Loaded challenge: {title}")
                        break
            
            self.game.right_panel.add_debug_message("New session started - challenges reset")
            return True
            
        # Test functions
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
            # Toggle help/debug panel or show help
            if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                # Shift+H toggles the right panel between help and debug
                self.game.right_panel.toggle_help()
                mode = "Help" if self.game.right_panel.show_help else "Debug"
                self.game.right_panel.add_debug_message(f"Right panel switched to {mode} mode")
            else:
                # Regular H shows help
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
        print("  L = Toggle leaderboard display")
        print("  G = Toggle debug mode for all components")
        print("  O = Toggle OPD display")
        print("  Shift+N = New session (reset score and challenges)")
        print("  Shift+H = Toggle help/debug panel")
        print("  T = Beam splitter direction test")
        print("  M = Multiple input port test")
        print("  R = Mirror reflection test")
        print("  H = Show this help")
        print("")
        print("Note: Shift+Click 'Clear All' button also resets completed challenges")
