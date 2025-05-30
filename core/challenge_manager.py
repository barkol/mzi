"""Challenge configuration and blocked field management."""
import json
import os
from utils.vector import Vector2
from config.settings import CANVAS_OFFSET_X, CANVAS_OFFSET_Y, GRID_SIZE

class ChallengeManager:
    """Manages challenge configurations and blocked fields."""
    
    def __init__(self):
        self.challenges = {}
        self.blocked_positions = []
        self.current_challenge = None
        self.load_challenges()
    
    def load_challenges(self):
        """Load challenge configurations from JSON file."""
        config_path = "config/challenges.json"
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    data = json.load(f)
                    self.challenges = data.get('challenges', {})
                    print(f"Loaded {len(self.challenges)} challenges")
            except Exception as e:
                print(f"Error loading challenges: {e}")
                self.challenges = self._get_default_challenges()
        else:
            print("No challenges.json found, using defaults")
            self.challenges = self._get_default_challenges()
            self._save_default_challenges()
    
    def _get_default_challenges(self):
        """Get default challenge configurations."""
        return {
            "basic_mz": {
                "name": "Basic Mach-Zehnder",
                "description": "Build a Mach-Zehnder interferometer with 2 beam splitters, 2 mirrors, and 2 detectors",
                "requirements": {
                    "beamsplitter": 2,
                    "mirror": 2,
                    "detector": 2
                },
                "min_components": 6,
                "max_components": 8,
                "points": 100,
                "bonus_conditions": [
                    {
                        "type": "interference",
                        "description": "Achieve interference at both detectors",
                        "points": 50
                    }
                ]
            },
            "triple_path": {
                "name": "Triple Path Interferometer",
                "description": "Create an interferometer with 3 different beam paths",
                "requirements": {
                    "beamsplitter": 3,
                    "mirror": 4,
                    "detector": 3
                },
                "min_components": 10,
                "max_components": 15,
                "points": 200,
                "bonus_conditions": [
                    {
                        "type": "all_detectors_active",
                        "description": "All detectors show signal",
                        "points": 100
                    }
                ]
            },
            "compact_mz": {
                "name": "Compact Design",
                "description": "Build a working MZ interferometer with minimal components",
                "requirements": {
                    "beamsplitter": 2,
                    "mirror": 2,
                    "detector": 1
                },
                "min_components": 5,
                "max_components": 5,
                "points": 150,
                "bonus_conditions": []
            }
        }
    
    def _save_default_challenges(self):
        """Save default challenges to file."""
        config_path = "config/challenges.json"
        os.makedirs("config", exist_ok=True)
        
        data = {
            "challenges": self._get_default_challenges(),
            "blocked_fields_file": "config/blocked_fields.txt"
        }
        
        try:
            with open(config_path, 'w') as f:
                json.dump(data, f, indent=2)
            print(f"Saved default challenges to {config_path}")
        except Exception as e:
            print(f"Error saving challenges: {e}")
    
    def load_blocked_fields(self, filename=None):
        """Load blocked field positions from text file."""
        if filename is None:
            filename = "config/blocked_fields.txt"
        
        self.blocked_positions.clear()
        
        if not os.path.exists(filename):
            print(f"No blocked fields file found at {filename}")
            return
        
        try:
            with open(filename, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        # Parse position: "x,y" or "grid_x,grid_y"
                        parts = line.split(',')
                        if len(parts) == 2:
                            try:
                                x = int(parts[0])
                                y = int(parts[1])
                                # Convert grid coordinates to screen coordinates
                                screen_x = CANVAS_OFFSET_X + x * GRID_SIZE
                                screen_y = CANVAS_OFFSET_Y + y * GRID_SIZE
                                self.blocked_positions.append(Vector2(screen_x, screen_y))
                            except ValueError:
                                print(f"Invalid position format: {line}")
            
            print(f"Loaded {len(self.blocked_positions)} blocked positions")
        except Exception as e:
            print(f"Error loading blocked fields: {e}")
    
    def create_blocked_fields_template(self):
        """Create a template blocked fields file."""
        template = """# Blocked Fields Configuration
# Format: grid_x,grid_y
# Grid coordinates start at 0,0 (top-left of canvas)
# Lines starting with # are comments

# Example: Block center area
10,7
10,8
10,9
11,7
11,8
11,9

# Example: Block corners
0,0
0,14
19,0
19,14
"""
        
        filename = "config/blocked_fields_template.txt"
        try:
            with open(filename, 'w') as f:
                f.write(template)
            print(f"Created blocked fields template at {filename}")
        except Exception as e:
            print(f"Error creating template: {e}")
    
    def is_position_blocked(self, x, y):
        """Check if a position is blocked."""
        test_pos = Vector2(x, y)
        for blocked_pos in self.blocked_positions:
            if blocked_pos.distance_to(test_pos) < GRID_SIZE / 2:
                return True
        return False
    
    def set_current_challenge(self, challenge_name):
        """Set the current challenge."""
        if challenge_name in self.challenges:
            self.current_challenge = challenge_name
            return True
        return False
    
    def check_setup(self, components, laser):
        """Check if current setup meets challenge requirements."""
        if not self.current_challenge:
            return False, "No challenge selected", 0
        
        challenge = self.challenges[self.current_challenge]
        
        # Count components by type
        component_counts = {}
        for comp in components:
            comp_type = comp.component_type
            component_counts[comp_type] = component_counts.get(comp_type, 0) + 1
        
        # Check basic requirements
        for comp_type, required_count in challenge['requirements'].items():
            if component_counts.get(comp_type, 0) < required_count:
                return False, f"Need at least {required_count} {comp_type}(s)", 0
        
        # Check component limits
        total_components = len(components)
        if total_components < challenge['min_components']:
            return False, f"Need at least {challenge['min_components']} components", 0
        if total_components > challenge['max_components']:
            return False, f"Maximum {challenge['max_components']} components allowed", 0
        
        # Basic requirements met
        points = challenge['points']
        messages = [f"Challenge '{challenge['name']}' completed! +{points} points"]
        
        # Check bonus conditions
        for bonus in challenge.get('bonus_conditions', []):
            if self._check_bonus_condition(bonus, components):
                points += bonus['points']
                messages.append(f"Bonus: {bonus['description']} +{bonus['points']} points")
        
        return True, "\n".join(messages), points
    
    def _check_bonus_condition(self, condition, components):
        """Check if a bonus condition is met."""
        if condition['type'] == 'interference':
            # Check if detectors show interference (varying intensity)
            detectors = [c for c in components if c.component_type == 'detector']
            active_detectors = [d for d in detectors if d.intensity > 0.01]
            return len(active_detectors) >= 2
        
        elif condition['type'] == 'all_detectors_active':
            # Check if all detectors have signal
            detectors = [c for c in components if c.component_type == 'detector']
            if not detectors:
                return False
            return all(d.intensity > 0.01 for d in detectors)
        
        return False
    
    def get_challenge_list(self):
        """Get list of available challenges."""
        return [(name, info['name']) for name, info in self.challenges.items()]
    
    def get_blocked_positions(self):
        """Get list of blocked positions."""
        return self.blocked_positions.copy()
