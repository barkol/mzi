# Mach-Zehnder Interferometer Game

An educational game for learning quantum optics by building a Mach-Zehnder interferometer.

## Features
- Drag-and-drop optical components
- Real-time beam tracing with quantum physics
- Phase control for interference patterns
- Visual feedback and scoring system
- Leaderboard for high scores
- Multiple challenges to complete

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
3. **Complete challenges** and earn points
4. **Submit high scores** to the leaderboard
5. **Click components** to remove them

## Controls

- **Left click**: Place/remove components
- **Clear All**: Remove all components
- **Check Setup**: Verify your interferometer
- **Toggle Laser**: Turn laser on/off
- **Leaderboard**: View high scores
- **L key**: Toggle leaderboard
- **H key**: Show help

## Physics

The game simulates real quantum optics:
- Green laser beams show coherent light paths
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
