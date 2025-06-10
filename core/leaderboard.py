"""Leaderboard management for high scores."""
import json
import os
from datetime import datetime
from typing import List, Dict, Tuple

class LeaderboardManager:
    """Manages high scores and leaderboard persistence."""
    
    def __init__(self, max_entries=10):
        self.max_entries = max_entries
        self.leaderboard_file = "leaderboard.json"
        self.entries = []
        self.load_leaderboard()
    
    def load_leaderboard(self):
        """Load leaderboard from file."""
        if os.path.exists(self.leaderboard_file):
            try:
                with open(self.leaderboard_file, 'r') as f:
                    data = json.load(f)
                    self.entries = data.get('entries', [])
                    # Ensure entries are sorted
                    self.entries.sort(key=lambda x: x['score'], reverse=True)
                    # Limit to max entries
                    self.entries = self.entries[:self.max_entries]
            except Exception as e:
                print(f"Error loading leaderboard: {e}")
                self.entries = []
        else:
            # Create default leaderboard with some initial scores
            self.entries = self._get_default_entries()
            self.save_leaderboard()
    
    def _get_default_entries(self) -> List[Dict]:
        """Get default leaderboard entries."""
        default_names = ["Alice", "Bob", "Charlie", "David", "Eve"]
        default_scores = [1000, 800, 600, 400, 200]
        default_fields = ["Treasure", "Maze", "Default Fields", "Default Fields", "Maze"]
        
        entries = []
        base_date = datetime.now()
        
        for i, (name, score, field) in enumerate(zip(default_names, default_scores, default_fields)):
            entries.append({
                'name': name,
                'score': score,
                'challenge': 'Basic MZ',
                'date': (base_date.replace(day=base_date.day - i)).isoformat(),
                'components': 6,
                'field_config': field
            })
        
        return entries
    
    def save_leaderboard(self):
        """Save leaderboard to file."""
        try:
            data = {
                'entries': self.entries,
                'last_updated': datetime.now().isoformat()
            }
            with open(self.leaderboard_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Error saving leaderboard: {e}")
    
    def add_score(self, name: str, score: int, challenge: str = None,
                  components: int = 0, field_config: str = None) -> Tuple[bool, int]:
        """
        Add a new score to the leaderboard.
        
        Returns:
            Tuple of (made_leaderboard, position)
        """
        # Create new entry
        entry = {
            'name': name[:20],  # Limit name length
            'score': score,
            'challenge': challenge or 'Free Play',
            'date': datetime.now().isoformat(),
            'components': components,
            'field_config': field_config or 'Default Fields'
        }
        
        # Find position
        position = -1
        for i, existing in enumerate(self.entries):
            if score > existing['score']:
                position = i
                break
        
        # If score is lower than all entries but we have space
        if position == -1 and len(self.entries) < self.max_entries:
            position = len(self.entries)
        
        # Add to leaderboard if qualified
        if position >= 0 and position < self.max_entries:
            self.entries.insert(position, entry)
            # Trim to max entries
            self.entries = self.entries[:self.max_entries]
            self.save_leaderboard()
            return True, position
        
        return False, -1
    
    def check_if_high_score(self, score: int) -> bool:
        """Check if a score qualifies for the leaderboard."""
        if len(self.entries) < self.max_entries:
            return True
        return score > self.entries[-1]['score']
    
    def get_entries(self) -> List[Dict]:
        """Get all leaderboard entries."""
        return self.entries.copy()
    
    def get_top_entries(self, count: int = 5) -> List[Dict]:
        """Get top N entries."""
        return self.entries[:min(count, len(self.entries))]
    
    def get_rank_for_score(self, score: int) -> int:
        """Get the rank a score would achieve (1-based)."""
        for i, entry in enumerate(self.entries):
            if score > entry['score']:
                return i + 1
        return len(self.entries) + 1
    
    def get_entries_for_map(self, field_config: str) -> List[Dict]:
        """Get leaderboard entries for a specific map."""
        return [entry for entry in self.entries 
                if entry.get('field_config', 'Default Fields') == field_config]
    
    def get_top_score_per_map(self) -> Dict[str, int]:
        """Get the top score for each map."""
        map_scores = {}
        for entry in self.entries:
            map_name = entry.get('field_config', 'Default Fields')
            current_score = map_scores.get(map_name, 0)
            map_scores[map_name] = max(current_score, entry['score'])
        return map_scores
    
    def clear_leaderboard(self):
        """Clear all entries (for testing/reset)."""
        self.entries = []
        self.save_leaderboard()
    
    def get_stats(self) -> Dict:
        """Get leaderboard statistics."""
        if not self.entries:
            return {
                'total_entries': 0,
                'highest_score': 0,
                'average_score': 0,
                'most_common_challenge': 'None',
                'most_common_map': 'None'
            }
        
        scores = [e['score'] for e in self.entries]
        challenges = [e['challenge'] for e in self.entries]
        maps = [e.get('field_config', 'Default Fields') for e in self.entries]
        
        # Count challenge frequency
        challenge_counts = {}
        for challenge in challenges:
            challenge_counts[challenge] = challenge_counts.get(challenge, 0) + 1
        
        # Count map frequency
        map_counts = {}
        for map_name in maps:
            map_counts[map_name] = map_counts.get(map_name, 0) + 1
        
        most_common_challenge = max(challenge_counts.items(), key=lambda x: x[1])[0]
        most_common_map = max(map_counts.items(), key=lambda x: x[1])[0]
        
        return {
            'total_entries': len(self.entries),
            'highest_score': max(scores),
            'average_score': sum(scores) // len(scores),
            'most_common_challenge': most_common_challenge,
            'most_common_map': most_common_map
        }