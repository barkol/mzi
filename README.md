# Mach-Zehnder Interferometer Game

An educational game for learning quantum optics by building a Mach-Zehnder interferometer.

## Features
- Drag-and-drop optical components
- Real-time beam tracing with quantum physics
- Phase control for interference patterns
- Visual feedback and scoring system

## Installation

1. Clone the repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Running the Game

```bash
python main.py
```

## How to Play

1. **Drag components** from the sidebar onto the grid
2. **Build an interferometer** using:
   - 2 beam splitters
   - 2 mirrors
   - 1 or more detectors
3. **Adjust the phase** slider to see interference effects
4. **Click components** to remove them

## Controls

- **Left click**: Place/remove components
- **Phase slider**: Control interference pattern
- **Clear All**: Remove all components
- **Check Setup**: Verify your interferometer
- **Toggle Laser**: Turn laser on/off

## Physics

The game simulates real quantum optics:
- Beam splitters create superposition states
- Phase differences create interference
- Detectors show intensity based on quantum amplitudes

## Project Structure

- `main.py`: Entry point
- `core/`: Game logic and physics
- `components/`: Optical components
- `ui/`: User interface elements
- `utils/`: Helper utilities
- `config/`: Game settings