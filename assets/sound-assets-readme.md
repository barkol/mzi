# Sound Assets Guide

This document describes the sound effects used in the Mach-Zehnder Interferometer Game.

## Directory Structure
```
assets/
└── sounds/
    ├── place_component.wav
    ├── remove_component.wav
    ├── invalid_placement.wav
    ├── drag_start.wav
    ├── drag_end.wav
    ├── laser_on.wav
    ├── laser_off.wav
    ├── beam_split.wav
    ├── beam_reflect.wav
    ├── beam_blocked.wav
    ├── detector_hit.wav
    ├── interference_constructive.wav
    ├── interference_destructive.wav
    ├── button_click.wav
    ├── button_hover.wav
    ├── panel_open.wav
    ├── panel_close.wav
    ├── challenge_complete.wav
    ├── challenge_failed.wav
    ├── bonus_achieved.wav
    ├── gold_field_hit.wav
    ├── high_score.wav
    ├── success.wav
    ├── error.wav
    ├── notification.wav
    └── ambient_hum.wav
```

## Sound Descriptions

### Component Sounds
- **place_component.wav**: Played when placing any component on the grid
- **remove_component.wav**: Played when removing a component
- **invalid_placement.wav**: Error sound for invalid placement attempts
- **drag_start.wav**: When starting to drag a component from sidebar
- **drag_end.wav**: When successfully placing a dragged component

### Laser & Beam Sounds
- **laser_on.wav**: Laser activation sound
- **laser_off.wav**: Laser deactivation sound
- **beam_split.wav**: When beam passes through beam splitter
- **beam_reflect.wav**: When beam reflects off mirror
- **beam_blocked.wav**: When beam hits blocked position

### Detection & Interference
- **detector_hit.wav**: Continuous sound scaled by detector intensity
- **interference_constructive.wav**: When beams interfere constructively
- **interference_destructive.wav**: When beams interfere destructively

### UI Sounds
- **button_click.wav**: Button press sound
- **button_hover.wav**: Mouse hover over button
- **panel_open.wav**: Opening panel/menu
- **panel_close.wav**: Closing panel/menu

### Feedback Sounds
- **challenge_complete.wav**: Challenge successfully completed
- **challenge_failed.wav**: Challenge requirements not met
- **bonus_achieved.wav**: Bonus condition achieved
- **gold_field_hit.wav**: Beam passes through gold field
- **high_score.wav**: New high score achieved
- **success.wav**: General success feedback
- **error.wav**: General error feedback
- **notification.wav**: General notification sound

### Ambient
- **ambient_hum.wav**: Background ambient sound (looped)

## Sound Guidelines

### Format Requirements
- Format: WAV (16-bit PCM)
- Sample Rate: 22050 Hz
- Channels: Stereo preferred, mono acceptable
- Duration: 
  - UI sounds: 50-200ms
  - Feedback sounds: 200-500ms
  - Success/complete sounds: 300-1000ms
  - Ambient: 2-5 seconds (loopable)

### Volume Guidelines
- UI sounds should be subtle (normalized to -12dB)
- Success/error sounds can be louder (-6dB)
- Ambient should be very quiet (-18dB)
- All sounds should avoid clipping

### Creating Custom Sounds
If creating custom sounds, consider:
- Keep them thematically consistent (electronic/sci-fi)
- Use similar frequency ranges for related sounds
- Add subtle reverb for spatial feel
- Ensure clean loops for continuous sounds

## Placeholder Sounds
The game will automatically generate simple placeholder sounds if the WAV files are missing. These are basic sine wave tones with different frequencies:
- Error sounds: 200Hz (low)
- Success sounds: 800Hz (high)
- Click sounds: 600Hz (mid)
- Laser sounds: 1000Hz
- Gold sounds: 1200Hz

## Implementation Notes
- The SoundManager handles all audio playback
- Master volume control is available (default: 0.7)
- Sounds can be toggled on/off globally
- Detector sounds automatically scale with intensity
- Multiple instances of the same sound can play simultaneously
