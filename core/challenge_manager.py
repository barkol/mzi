"""Challenge configuration and blocked/gold field management with improved interference detection."""
import json
import os
import glob
from utils.vector import Vector2
from config.settings import CANVAS_OFFSET_X, CANVAS_OFFSET_Y, GRID_SIZE

class ChallengeManager:
    """Manages challenge configurations, blocked fields, and gold fields."""
    
    def __init__(self):
        self.challenges = {}
        self.blocked_positions = []
        self.gold_positions = []  # New: Gold field positions
        self.current_challenge = None
        self.current_field_config = "default"  # Track current field configuration
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
                "points": 0,  # Not used anymore - score based on detector power
                "bonus_conditions": [
                    {
                        "type": "interference",
                        "description": "Achieve interference (2+ beams enter same beam splitter)",
                        "points": 200
                    }
                ]
            },
            "gold_rush": {
                "name": "Gold Rush Challenge",
                "description": "Build an interferometer that passes beams through gold fields for bonus points",
                "requirements": {
                    "beamsplitter": 2,
                    "mirror": 3,
                    "detector": 2
                },
                "min_components": 7,
                "max_components": 10,
                "points": 0,  # Not used anymore
                "bonus_conditions": [
                    {
                        "type": "gold_fields",
                        "description": "Pass beams through gold fields",
                        "points": 0  # Dynamic based on intensity
                    },
                    {
                        "type": "interference",
                        "description": "Achieve interference",
                        "points": 100
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
                "points": 0,  # Not used anymore
                "bonus_conditions": [
                    {
                        "type": "all_detectors_active",
                        "description": "All detectors show signal",
                        "points": 300
                    },
                    {
                        "type": "multi_port_interference",
                        "description": "3+ beams interfere in one component",
                        "points": 500
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
                "points": 0,  # Not used anymore
                "bonus_conditions": [
                    {
                        "type": "interference",
                        "description": "Achieve interference",
                        "points": 300
                    },
                    {
                        "type": "efficiency",
                        "description": "Achieve >90% detector efficiency",
                        "points": 200
                    }
                ]
            },
            "maximum_power": {
                "name": "Maximum Power",
                "description": "Maximize total detector power using constructive interference",
                "requirements": {
                    "beamsplitter": 2,
                    "mirror": 2,
                    "detector": 1
                },
                "min_components": 5,
                "max_components": 12,
                "points": 0,
                "bonus_conditions": [
                    {
                        "type": "high_power",
                        "description": "Achieve total detector power > 1.8",
                        "points": 500
                    },
                    {
                        "type": "constructive_interference",
                        "description": "All interfering beams are in phase",
                        "points": 500
                    }
                ]
            },
            "interference_explorer": {
                "name": "Interference Explorer",
                "description": "Create multiple interference points in your setup",
                "requirements": {
                    "beamsplitter": 4,
                    "mirror": 2,
                    "detector": 4
                },
                "min_components": 10,
                "max_components": 20,
                "points": 0,
                "bonus_conditions": [
                    {
                        "type": "multiple_interference_points",
                        "description": "Create interference at 3+ beam splitters",
                        "points": 1000
                    }
                ]
            }
        }
    
    def _save_default_challenges(self):
        """Save default challenges to file."""
        config_path = "config/challenges.json"
        os.makedirs("config", exist_ok=True)
        
        data = {
            "challenges": self._get_default_challenges(),
            "blocked_fields_file": "config/blocked_fields.txt",
            "gold_fields_file": "config/gold_fields.txt"  # New: Add gold fields file
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
            skipped_conflicts = 0
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
                                new_pos = Vector2(screen_x, screen_y)
                                
                                # Check if this position is already a gold field
                                if self.is_position_gold(screen_x, screen_y):
                                    print(f"Warning: Blocked field at ({x},{y}) conflicts with gold field - skipping")
                                    skipped_conflicts += 1
                                else:
                                    self.blocked_positions.append(new_pos)
                            except ValueError:
                                print(f"Invalid position format: {line}")
            
            print(f"Loaded {len(self.blocked_positions)} blocked positions")
            if skipped_conflicts > 0:
                print(f"Skipped {skipped_conflicts} blocked fields due to conflicts with gold fields")
        except Exception as e:
            print(f"Error loading blocked fields: {e}")
    
    def load_gold_fields(self, filename=None):
        """Load gold field positions from text file."""
        if filename is None:
            filename = "config/gold_fields.txt"
        
        self.gold_positions.clear()
        
        if not os.path.exists(filename):
            print(f"No gold fields file found at {filename}")
            # Create default gold fields file
            self.create_gold_fields_template()
            return
        
        try:
            skipped_conflicts = 0
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
                                new_pos = Vector2(screen_x, screen_y)
                                
                                # Check if this position is already blocked
                                if self.is_position_blocked(screen_x, screen_y):
                                    print(f"Warning: Gold field at ({x},{y}) conflicts with blocked field - skipping")
                                    skipped_conflicts += 1
                                else:
                                    self.gold_positions.append(new_pos)
                            except ValueError:
                                print(f"Invalid position format: {line}")
            
            print(f"Loaded {len(self.gold_positions)} gold positions")
            if skipped_conflicts > 0:
                print(f"Skipped {skipped_conflicts} gold fields due to conflicts with blocked fields")
        except Exception as e:
            print(f"Error loading gold fields: {e}")
    
    def get_available_field_configs(self):
        """Get list of available field configuration files."""
        configs = []
        
        # Default configuration
        configs.append({
            'name': 'default',
            'display_name': 'Default Fields',
            'blocked_file': 'config/blocked_fields.txt',
            'gold_file': 'config/gold_fields.txt'
        })
        
        # Look for other field configuration files in config directory
        # Find all blocked field files
        blocked_files = glob.glob('config/blocked_fields_*.txt')
        for blocked_file in blocked_files:
            # Extract name from filename
            name = blocked_file.replace('config/blocked_fields_', '').replace('.txt', '')
            display_name = name.replace('_', ' ').title()
            
            # Check if corresponding gold file exists
            gold_file = f'config/gold_fields_{name}.txt'
            if not os.path.exists(gold_file):
                gold_file = 'config/gold_fields.txt'  # Use default gold fields
            
            configs.append({
                'name': name,
                'display_name': display_name,
                'blocked_file': blocked_file,
                'gold_file': gold_file
            })
        
        # Find all gold field files without corresponding blocked files
        gold_files = glob.glob('config/gold_fields_*.txt')
        for gold_file in gold_files:
            name = gold_file.replace('config/gold_fields_', '').replace('.txt', '')
            # Skip if we already have this config from blocked files
            if any(c['name'] == name for c in configs):
                continue
                
            display_name = name.replace('_', ' ').title()
            configs.append({
                'name': name,
                'display_name': display_name,
                'blocked_file': 'config/blocked_fields.txt',  # Use default blocked fields
                'gold_file': gold_file
            })
        
        # Add example configurations if they exist
        example_configs = [
            {
                'name': 'example',
                'display_name': 'Example Layout',
                'blocked_file': 'config/example_blocked_fields.txt',
                'gold_file': 'config/example_gold_fields.txt'
            },
            {
                'name': 'maze',
                'display_name': 'Beam Maze',
                'blocked_file': 'config/blocked_fields_maze.txt',
                'gold_file': 'config/gold_fields.txt'
            },
            {
                'name': 'treasure',
                'display_name': 'Treasure Hunt',
                'blocked_file': 'config/blocked_fields.txt',
                'gold_file': 'config/gold_fields_treasure.txt'
            }
        ]
        
        for config in example_configs:
            # Only add if files exist and not already in list
            if (os.path.exists(config['blocked_file']) or os.path.exists(config['gold_file'])) \
               and not any(c['name'] == config['name'] for c in configs):
                # Use default files if specific ones don't exist
                if not os.path.exists(config['blocked_file']):
                    config['blocked_file'] = 'config/blocked_fields.txt'
                if not os.path.exists(config['gold_file']):
                    config['gold_file'] = 'config/gold_fields.txt'
                configs.append(config)
        
        return configs
    
    def load_field_config(self, config_name):
        """Load a specific field configuration by name."""
        configs = self.get_available_field_configs()
        
        # Find the requested configuration
        config = None
        for c in configs:
            if c['name'] == config_name:
                config = c
                break
        
        if not config:
            print(f"Field configuration '{config_name}' not found")
            return False
        
        try:
            # Clear existing field positions
            self.blocked_positions.clear()
            self.gold_positions.clear()
            
            # Load new field configurations
            print(f"\nLoading field configuration: {config['display_name']}")
            
            # Load gold fields first (so blocked fields can override)
            if os.path.exists(config['gold_file']):
                self.load_gold_fields(config['gold_file'])
            else:
                print(f"Gold fields file not found: {config['gold_file']}")
            
            # Load blocked fields second
            if os.path.exists(config['blocked_file']):
                self.load_blocked_fields(config['blocked_file'])
            else:
                print(f"Blocked fields file not found: {config['blocked_file']}")
            
            # Validate the configuration
            self.validate_field_configurations()
            
            # Update current configuration
            self.current_field_config = config_name
            
            print(f"Successfully loaded field configuration: {config['display_name']}")
            return True
            
        except Exception as e:
            print(f"Error loading field configuration: {e}")
            # Restore default configuration on error
            self.load_blocked_fields()
            self.load_gold_fields()
            self.current_field_config = "default"
            return False
    
    def create_blocked_fields_template(self):
        """Create a template blocked fields file."""
        template = """# Blocked Fields Configuration
# Format: grid_x,grid_y
# Grid coordinates start at 0,0 (top-left of canvas)
# Lines starting with # are comments

# IMPORTANT: A field cannot be both blocked AND gold!
# If a position appears in both blocked_fields.txt and gold_fields.txt,
# the blocked field takes precedence (the position will be blocked, not gold).

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
    
    def create_gold_fields_template(self):
        """Create a template gold fields file."""
        template = """# Gold Fields Configuration
# These fields award 100 points × beam intensity when beams pass through
# Format: grid_x,grid_y
# Grid coordinates start at 0,0 (top-left of canvas)
# Canvas is 20x15 grid cells (800x600 pixels with 40px grid)
# Lines starting with # are comments

# IMPORTANT: A field cannot be both blocked AND gold!
# If a position appears in both blocked_fields.txt and gold_fields.txt,
# the blocked field takes precedence (the position will be blocked, not gold).

# Example: Strategic gold field placements

# Upper path rewards
7,5
8,5
9,5

# Lower path rewards
7,11
8,11
9,11

# Central challenge areas (avoid if these are blocked!)
10,7
10,8
10,9

# High-value corner positions
2,2
17,2
2,12
17,12

# Intersection bonuses
12,7
14,8

# Note: Gold fields can overlap with component positions
# The bonus is awarded based on beam paths, not component placement
"""
        
        filename = "config/gold_fields.txt"
        try:
            with open(filename, 'w') as f:
                f.write(template)
            print(f"Created gold fields template at {filename}")
        except Exception as e:
            print(f"Error creating template: {e}")
    
    def is_position_blocked(self, x, y):
        """Check if a position is blocked."""
        test_pos = Vector2(x, y)
        for blocked_pos in self.blocked_positions:
            if blocked_pos.distance_to(test_pos) < GRID_SIZE / 2:
                return True
        return False
    
    def is_position_gold(self, x, y):
        """Check if a position is a gold field."""
        test_pos = Vector2(x, y)
        for gold_pos in self.gold_positions:
            if gold_pos.distance_to(test_pos) < GRID_SIZE / 2:
                return True
        return False
    
    def set_current_challenge(self, challenge_name):
        """Set the current challenge."""
        if challenge_name in self.challenges:
            self.current_challenge = challenge_name
            return True
        return False
    
    def check_setup(self, components, laser, beam_tracer=None):
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
        
        # Calculate base score from detector power
        detectors = [c for c in components if c.component_type == 'detector']
        total_detector_power = sum(d.intensity for d in detectors)
        base_score = round(total_detector_power * 1000)  # FIXED: Use round() instead of int()
        
        # Start with base score instead of challenge points
        points = base_score
        messages = [f"Challenge '{challenge['name']}' completed!"]
        messages.append(f"Detector Power Score: {base_score} points ({total_detector_power:.2f} × 1000)")
        
        # Check bonus conditions
        for bonus in challenge.get('bonus_conditions', []):
            bonus_points, bonus_msg = self._check_bonus_condition(bonus, components, beam_tracer)
            if bonus_points > 0:
                points += bonus_points
                messages.append(bonus_msg)
        
        # Calculate gold field bonus if beam tracer is provided
        if beam_tracer and hasattr(beam_tracer, 'gold_field_hits'):
            gold_bonus = self.calculate_gold_field_bonus(beam_tracer.gold_field_hits)
            if gold_bonus > 0:
                points += gold_bonus
                messages.append(f"Gold Field Bonus: +{gold_bonus} points")
        
        # Add total score summary
        messages.append(f"Total Score: {points} points")
        
        return True, "\n".join(messages), points
    
    def _check_bonus_condition(self, condition, components, beam_tracer=None):
        """Check if a bonus condition is met."""
        if condition['type'] == 'interference':
            # Check if any beam splitter has beams from multiple ports
            beam_splitters = [c for c in components if c.component_type == 'beamsplitter']
            for bs in beam_splitters:
                if hasattr(bs, 'all_beams_by_port'):
                    # Count how many ports have beams
                    ports_with_beams = 0
                    for port_beams in bs.all_beams_by_port.values():
                        if len(port_beams) > 0:
                            ports_with_beams += 1
                    
                    # Interference happens when beams enter from 2+ different ports
                    if ports_with_beams >= 2:
                        return condition['points'], f"Bonus: {condition['description']} +{condition['points']} points"
            return 0, ""
        
        elif condition['type'] == 'multi_port_interference':
            # Check for 3+ beams interfering
            beam_splitters = [c for c in components if c.component_type == 'beamsplitter']
            for bs in beam_splitters:
                if hasattr(bs, 'all_beams_by_port'):
                    ports_with_beams = 0
                    for port_beams in bs.all_beams_by_port.values():
                        if len(port_beams) > 0:
                            ports_with_beams += 1
                    
                    if ports_with_beams >= 3:
                        return condition['points'], f"Bonus: {condition['description']} +{condition['points']} points"
            return 0, ""
        
        elif condition['type'] == 'multiple_interference_points':
            # Count beam splitters with interference
            beam_splitters = [c for c in components if c.component_type == 'beamsplitter']
            interference_count = 0
            
            for bs in beam_splitters:
                if hasattr(bs, 'all_beams_by_port'):
                    ports_with_beams = 0
                    for port_beams in bs.all_beams_by_port.values():
                        if len(port_beams) > 0:
                            ports_with_beams += 1
                    
                    if ports_with_beams >= 2:
                        interference_count += 1
            
            if interference_count >= 3:
                return condition['points'], f"Bonus: {condition['description']} +{condition['points']} points"
            return 0, ""
        
        elif condition['type'] == 'constructive_interference':
            # Check if interfering beams are in phase
            import math
            beam_splitters = [c for c in components if c.component_type == 'beamsplitter']
            
            for bs in beam_splitters:
                if hasattr(bs, 'all_beams_by_port'):
                    # Get all beams entering this beam splitter
                    all_phases = []
                    ports_with_beams = 0
                    
                    for port_beams in bs.all_beams_by_port.values():
                        if port_beams:
                            ports_with_beams += 1
                            for beam in port_beams:
                                phase = beam.get('accumulated_phase', beam.get('phase', 0))
                                all_phases.append(phase % (2 * math.pi))
                    
                    # Check if we have interference (2+ ports)
                    if ports_with_beams >= 2 and len(all_phases) >= 2:
                        # Check if all phases are similar (within π/4)
                        phase_spread = max(all_phases) - min(all_phases)
                        if phase_spread < math.pi / 4:
                            return condition['points'], f"Bonus: {condition['description']} +{condition['points']} points"
            return 0, ""
        
        elif condition['type'] == 'all_detectors_active':
            # Check if all detectors have signal
            detectors = [c for c in components if c.component_type == 'detector']
            if detectors and all(d.intensity > 0.01 for d in detectors):
                return condition['points'], f"Bonus: {condition['description']} +{condition['points']} points"
        
        elif condition['type'] == 'gold_fields':
            # Gold field bonus is calculated separately
            return 0, ""
        
        elif condition['type'] == 'efficiency':
            # Check if any detector has >90% efficiency
            detectors = [c for c in components if c.component_type == 'detector']
            if any(d.intensity > 0.9 for d in detectors):
                return condition['points'], f"Bonus: {condition['description']} +{condition['points']} points"
        
        elif condition['type'] == 'high_power':
            # Check if total detector power exceeds threshold
            detectors = [c for c in components if c.component_type == 'detector']
            total_power = sum(d.intensity for d in detectors)
            # Adjusted threshold for more realistic power levels
            if total_power > 1.8:  # Changed from 3.5 to 1.8
                return condition['points'], f"Bonus: {condition['description']} +{condition['points']} points"
        
        return 0, ""
    
    def calculate_gold_field_bonus(self, gold_field_hits):
        """Calculate bonus points from gold field hits."""
        total_bonus = 0
        for position, intensity in gold_field_hits.items():
            # 100 points per unit of intensity - use round() for proper rounding
            bonus = round(intensity * 100)  # FIXED: Use round() instead of int()
            total_bonus += bonus
        return total_bonus
    
    def validate_field_configurations(self):
        """Validate that there are no conflicts between blocked and gold fields."""
        conflicts = []
        
        for gold_pos in self.gold_positions:
            for blocked_pos in self.blocked_positions:
                if gold_pos.distance_to(blocked_pos) < GRID_SIZE / 2:
                    # Convert back to grid coordinates for reporting
                    gold_grid_x = round((gold_pos.x - CANVAS_OFFSET_X) / GRID_SIZE)
                    gold_grid_y = round((gold_pos.y - CANVAS_OFFSET_Y) / GRID_SIZE)
                    blocked_grid_x = round((blocked_pos.x - CANVAS_OFFSET_X) / GRID_SIZE)
                    blocked_grid_y = round((blocked_pos.y - CANVAS_OFFSET_Y) / GRID_SIZE)
                    
                    conflicts.append({
                        'gold': (gold_grid_x, gold_grid_y),
                        'blocked': (blocked_grid_x, blocked_grid_y)
                    })
        
        if conflicts:
            print(f"\nWARNING: Found {len(conflicts)} position conflicts!")
            print("The following positions are defined as both gold and blocked:")
            for conflict in conflicts:
                print(f"  Grid position ({conflict['gold'][0]},{conflict['gold'][1]})")
            print("Blocked fields take precedence - these positions will be blocked, not gold.")
        else:
            print("Field configuration validated - no conflicts found.")
        
        return len(conflicts) == 0
    
    def get_challenge_list(self):
        """Get list of available challenges."""
        return [(name, info['name']) for name, info in self.challenges.items()]
    
    def get_blocked_positions(self):
        """Get list of blocked positions."""
        return self.blocked_positions.copy()
    
    def get_gold_positions(self):
        """Get list of gold positions."""
        return self.gold_positions.copy()