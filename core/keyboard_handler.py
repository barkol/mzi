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
                        self.game.current_challenge_display_name = title
                        self.game.controls.set_challenge(title)
                        if hasattr(self.game.controls, 'set_challenge_completed'):
                            self.game.controls.set_challenge_completed(False)  # Reset gold color
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
        print("\n=== CONTROLS & HELP ===")
        print("")
        print("Key bindings:")
        print("  F11 = Toggle fullscreen (windowed mode only)")
        print("  ESC = Exit fullscreen")
        print("  L = Toggle leaderboard display")
        print("  G = Toggle debug mode for all components")
        print("  O = Toggle OPD display")
        print("  Shift+N = New session (reset score and challenges)")
        print("  Shift+H = Toggle help/debug panel")
        print("  H = Show this help")
        print("")
        print("Window modes:")
        print("  python main.py              - Default windowed mode")
        print("  python main.py --fullscreen - Fullscreen mode")
        print("  python main.py --scale      - Scaled to fit screen")
        print("")
        print("Mouse controls:")
        print("  Drag & Drop - Place components from sidebar")
        print("  Left Click  - Remove component from canvas")
        print("")
        print("Game tips:")
        print("  - Build a Mach-Zehnder interferometer with 2 beam splitters and 2 mirrors")
        print("  - Gold fields award bonus points based on beam intensity")
        print("  - Completed challenges turn gold and award points only once per session")
        print("  - Use Shift+Click on 'Clear All' to reset completed challenges")
