"""Sound manager for handling game audio effects with better error handling."""
import pygame
import os
from typing import Dict, Optional
import sys

class SoundManager:
    """Manages all sound effects for the game."""
    
    def __init__(self, volume: float = 0.7):
        """Initialize the sound manager.
        
        Args:
            volume: Master volume (0.0 to 1.0)
        """
        self.sounds: Dict[str, pygame.mixer.Sound] = {}
        self.enabled = True
        self.master_volume = volume
        self.assets_path = "assets/sounds"
        
        # Initialize pygame mixer with fallback options
        self._init_mixer()
        
        # Define sound files to load
        self.sound_files = {
            # Component interactions
            'place_component': 'place_component.wav',
            'remove_component': 'remove_component.wav',
            'invalid_placement': 'invalid_placement.wav',
            'drag_start': 'drag_start.wav',
            'drag_end': 'drag_end.wav',
            
            # Laser and beam
            'laser_on': 'laser_on.wav',
            'laser_off': 'laser_off.wav',
            'beam_split': 'beam_split.wav',
            'beam_reflect': 'beam_reflect.wav',
            'beam_blocked': 'beam_blocked.wav',
            
            # Detector and interference
            'detector_hit': 'detector_hit.wav',
            'interference_constructive': 'interference_constructive.wav',
            'interference_destructive': 'interference_destructive.wav',
            
            # UI interactions
            'button_click': 'button_click.wav',
            'button_hover': 'button_hover.wav',
            'panel_open': 'panel_open.wav',
            'panel_close': 'panel_close.wav',
            
            # Challenge and scoring
            'challenge_complete': 'challenge_complete.wav',
            'challenge_failed': 'challenge_failed.wav',
            'bonus_achieved': 'bonus_achieved.wav',
            'gold_field_hit': 'gold_field_hit.wav',
            'high_score': 'high_score.wav',
            
            # Feedback
            'success': 'success.wav',
            'error': 'error.wav',
            'notification': 'notification.wav',
            
            # Ambient
            'ambient_hum': 'ambient_hum.wav'  # Optional background ambience
        }
        
        # Load all sounds
        self._ensure_sounds_folder()
        self._load_sounds()
        
        # Track currently playing sounds for management
        self.active_channels: Dict[str, pygame.mixer.Channel] = {}
        
        # Special handling for continuous sounds
        self.continuous_sounds = {'ambient_hum', 'detector_hit'}
        self.detector_channels: Dict[int, pygame.mixer.Channel] = {}  # Track detector sounds by ID
        self.active_detectors: set = set()  # Track which detectors are active
        
        # Report initialization status
        print(f"Sound Manager initialized: {len(self.sounds)} sounds loaded")
        if not self.sounds:
            print("WARNING: No sounds were loaded! Check your assets/sounds folder.")
    
    def _init_mixer(self):
        """Initialize pygame mixer with fallback options."""
        # Try different initialization parameters
        init_params = [
            {'frequency': 22050, 'size': -16, 'channels': 2, 'buffer': 512},
            {'frequency': 44100, 'size': -16, 'channels': 2, 'buffer': 512},
            {'frequency': 22050, 'size': -16, 'channels': 1, 'buffer': 512},
            {},  # Use pygame defaults
        ]
        
        for params in init_params:
            try:
                pygame.mixer.quit()  # Ensure clean state
                pygame.mixer.init(**params)
                
                # Test if initialization worked
                if pygame.mixer.get_init():
                    print(f"Pygame mixer initialized with: {pygame.mixer.get_init()}")
                    return
            except pygame.error as e:
                print(f"Mixer init failed with {params}: {e}")
                continue
        
        # If all attempts failed
        print("ERROR: Could not initialize pygame mixer! Sound will be disabled.")
        self.enabled = False
    
    def _ensure_sounds_folder(self):
        """Ensure the sounds folder exists."""
        if not os.path.exists(self.assets_path):
            os.makedirs(self.assets_path)
            print(f"Created sounds folder at: {self.assets_path}")
            self._create_placeholder_sounds()
    
    def _create_placeholder_sounds(self):
        """Create placeholder sound files for testing."""
        print("Note: No sound files found. Using silent placeholders.")
        print(f"Add .wav files to '{self.assets_path}' folder for actual sounds.")
        
        # Create a silent sound as placeholder
        if pygame.mixer.get_init():
            # Create 0.1 second of silence
            sample_rate = pygame.mixer.get_init()[0]
            samples = int(sample_rate * 0.1)
            
            # Create silent array
            import array
            silence = array.array('h', [0] * samples * 2)  # Stereo
            
            # Create sound object
            silent_sound = pygame.sndarray.make_sound(silence)
            
            # Use this for all sounds
            for sound_name in self.sound_files:
                self.sounds[sound_name] = silent_sound
    
    def _load_sounds(self):
        """Load all sound files into memory."""
        if not self.enabled:
            return
            
        loaded_count = 0
        
        for sound_name, filename in self.sound_files.items():
            filepath = os.path.join(self.assets_path, filename)
            
            try:
                if os.path.exists(filepath):
                    # Check file size
                    file_size = os.path.getsize(filepath)
                    if file_size == 0:
                        print(f"Warning: {filename} is empty (0 bytes)")
                        continue
                    
                    sound = pygame.mixer.Sound(filepath)
                    sound.set_volume(self.master_volume)
                    self.sounds[sound_name] = sound
                    loaded_count += 1
                    print(f"Loaded sound: {sound_name} ({file_size/1024:.1f} KB)")
                else:
                    # Don't print for every missing file in normal operation
                    if loaded_count == 0 and sound_name == list(self.sound_files.keys())[0]:
                        print(f"No sound files found in {self.assets_path}")
            except pygame.error as e:
                print(f"Error loading {filename}: {e}")
            except Exception as e:
                print(f"Unexpected error loading {filename}: {e}")
        
        # If no sounds were loaded, create placeholders
        if loaded_count == 0:
            self._create_placeholder_sounds()
        else:
            print(f"Successfully loaded {loaded_count} sound files")
    
    def play(self, sound_name: str, volume: Optional[float] = None,
             loops: int = 0, fade_ms: int = 0) -> Optional[pygame.mixer.Channel]:
        """Play a sound effect.
        
        Args:
            sound_name: Name of the sound to play
            volume: Override volume for this playback (0.0 to 1.0)
            loops: Number of times to loop (-1 for infinite)
            fade_ms: Fade in duration in milliseconds
            
        Returns:
            The channel playing the sound, or None if not played
        """
        if not self.enabled:
            return None
            
        if sound_name not in self.sounds:
            # Don't spam console with missing sound warnings
            return None
        
        try:
            sound = self.sounds[sound_name]
            
            # Set volume for this playback
            if volume is not None:
                sound.set_volume(volume * self.master_volume)
            else:
                sound.set_volume(self.master_volume)
            
            # Play the sound
            if fade_ms > 0:
                channel = sound.play(loops, fade_ms=fade_ms)
            else:
                channel = sound.play(loops)
            
            # Track continuous sounds
            if sound_name in self.continuous_sounds and channel:
                self.active_channels[sound_name] = channel
            
            return channel
            
        except pygame.error as e:
            print(f"Error playing sound {sound_name}: {e}")
            return None
    
    def stop(self, sound_name: str, fade_ms: int = 0):
        """Stop a specific sound.
        
        Args:
            sound_name: Name of the sound to stop
            fade_ms: Fade out duration in milliseconds
        """
        if sound_name in self.active_channels:
            channel = self.active_channels[sound_name]
            try:
                if channel.get_busy():
                    if fade_ms > 0:
                        channel.fadeout(fade_ms)
                    else:
                        channel.stop()
            except:
                pass
            del self.active_channels[sound_name]
    
    def stop_all(self, fade_ms: int = 0):
        """Stop all currently playing sounds."""
        try:
            if fade_ms > 0:
                pygame.mixer.fadeout(fade_ms)
            else:
                pygame.mixer.stop()
        except:
            pass
        self.active_channels.clear()
        self.detector_channels.clear()
        self.active_detectors.clear()
    
    def set_volume(self, volume: float):
        """Set the master volume.
        
        Args:
            volume: Volume level (0.0 to 1.0)
        """
        self.master_volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            try:
                sound.set_volume(self.master_volume)
            except:
                pass
    
    def toggle_enabled(self):
        """Toggle sound on/off."""
        self.enabled = not self.enabled
        if not self.enabled:
            self.stop_all()
        print(f"Sound: {'ON' if self.enabled else 'OFF'}")
    
    def update_detector_sound(self, detector_id: int, intensity: float, position: tuple):
        """Update detector sound based on intensity - DISABLED as it's too annoying."""
        # This function is now disabled to prevent constant detector sounds
        # Clean up any existing detector sounds
        if detector_id in self.detector_channels:
            channel = self.detector_channels[detector_id]
            try:
                if channel.get_busy():
                    channel.stop()
            except:
                pass
            del self.detector_channels[detector_id]
        
        # Remove from active detectors
        self.active_detectors.discard(detector_id)
        return
    
    def cleanup_detector_sounds(self, active_detector_ids: set):
        """Clean up sounds for removed detectors - DISABLED as detector sounds are disabled.
        
        Args:
            active_detector_ids: Set of currently active detector IDs
        """
        # This function is disabled since we're not using detector sounds anymore
        # Clean up any remaining detector sounds
        if self.detector_channels:
            for detector_id in list(self.detector_channels.keys()):
                channel = self.detector_channels[detector_id]
                try:
                    if channel.get_busy():
                        channel.stop()
                except:
                    pass
            self.detector_channels.clear()
            self.active_detectors.clear()

    def play_interference_sound(self, constructive: bool):
        """Play interference sound based on type.
        
        Args:
            constructive: True for constructive, False for destructive
        """
        if constructive:
            self.play('interference_constructive', volume=0.8)
        else:
            self.play('interference_destructive', volume=0.6)
    
    def play_ui_feedback(self, success: bool):
        """Play UI feedback sound.
        
        Args:
            success: True for success, False for error
        """
        if success:
            self.play('success', volume=0.6)
        else:
            self.play('error', volume=0.7)
    
    def start_ambient(self):
        """Start ambient background sound."""
        self.play('ambient_hum', volume=0.2, loops=-1, fade_ms=2000)
    
    def stop_ambient(self):
        """Stop ambient background sound."""
        self.stop('ambient_hum', fade_ms=2000)
