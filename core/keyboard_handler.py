"""Keyboard command handler for debug and test functions."""
import pygame
import math
import cmath
from core.test_utilities import TestUtilities
from utils.energy_checker import check_energy_conservation, EnergyMonitor

class KeyboardHandler:
    """Handles keyboard shortcuts and debug commands."""
    
    def __init__(self, game):
        self.game = game
        self.tests = TestUtilities()
        self.energy_monitor = EnergyMonitor()
    
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
            
        elif event.key == pygame.K_s and pygame.key.get_mods() & pygame.KMOD_SHIFT:
            # Shift+S - Toggle sound
            self.game.sound_manager.toggle_enabled()
            status = "ON" if self.game.sound_manager.enabled else "OFF"
            print(f"Sound: {status}")
            self.game.right_panel.add_debug_message(f"Sound: {status}")
            if self.game.sound_manager.enabled:
                self.game.sound_manager.play('notification')
                self.game.sound_manager.start_ambient()
            return True
            
        elif event.key == pygame.K_v and pygame.key.get_mods() & pygame.KMOD_SHIFT:
            # Shift+V - Volume control
            if pygame.key.get_mods() & pygame.KMOD_CTRL:
                # Ctrl+Shift+V - Decrease volume
                new_volume = max(0.0, self.game.sound_manager.master_volume - 0.1)
            else:
                # Shift+V - Increase volume
                new_volume = min(1.0, self.game.sound_manager.master_volume + 0.1)
            
            self.game.sound_manager.set_volume(new_volume)
            print(f"Volume: {int(new_volume * 100)}%")
            self.game.right_panel.add_debug_message(f"Volume: {int(new_volume * 100)}%")
            self.game.sound_manager.play('button_click')
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
            
        # Energy conservation check
        elif event.key == pygame.K_e:
            if pygame.key.get_mods() & pygame.KMOD_SHIFT:
                # Shift+E - Toggle energy monitor overlay
                enabled = self.energy_monitor.toggle()
                print(f"Energy monitor: {'ON' if enabled else 'OFF'}")
                self.game.right_panel.add_debug_message(f"Energy monitor: {'ON' if enabled else 'OFF'}")
            else:
                # E - Run detailed energy conservation analysis
                check_energy_conservation(
                    self.game.component_manager.components,
                    self.game.laser,
                    self.game.beam_tracer
                )
                self.game.right_panel.add_debug_message("Energy conservation analysis (see console)")
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
            self.game.sound_manager.play('notification')
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
                self.game.sound_manager.play('panel_open')
            else:
                # Regular H shows help
                self._show_help()
            return True
            
        return False
    
    def update(self):
        """Update keyboard handler components."""
        # Update energy monitor if enabled
        if self.energy_monitor.enabled:
            self.energy_monitor.update(
                self.game.component_manager.components,
                self.game.laser,
                self.game.beam_tracer
            )
    
    def draw(self, screen):
        """Draw keyboard handler overlays."""
        # Draw energy monitor if enabled
        self.energy_monitor.draw(screen)
    
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
        print("  E = Energy conservation analysis")
        print("  Shift+E = Toggle energy monitor overlay")
        print("  Shift+S = Toggle sound on/off")
        print("  Shift+V = Increase volume")
        print("  Ctrl+Shift+V = Decrease volume")
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
        print("")
        print("Energy Conservation:")
        print("  - Press 'E' for detailed energy analysis in console")
        print("  - Press 'Shift+E' to toggle on-screen energy monitor")
        print("  - Local energy at detectors varies with interference")
        print("  - Global energy across all detectors should equal input")
        print("")
        print("Sound controls:")
        print("  - Shift+S toggles all sound effects on/off")
        print("  - Shift+V increases volume by 10%")
        print("  - Ctrl+Shift+V decreases volume by 10%")
        print("  - Current volume: {}%".format(int(self.game.sound_manager.master_volume * 100)))