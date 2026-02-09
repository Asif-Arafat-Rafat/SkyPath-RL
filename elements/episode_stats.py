"""
Episode Statistics Logger
Tracks episode performance metrics and saves to JSON
"""
import json
import os
from datetime import datetime

class EpisodeStatsLogger:
    def __init__(self, log_file="communication_logs/episode_stats.json"):
        self.log_file = log_file
        self.episodes = []
        
        # Ensure directory exists
        d = os.path.dirname(log_file)
        if d and not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
        
        # Load existing episodes if file exists
        try:
            if os.path.exists(self.log_file):
                with open(self.log_file, 'r') as f:
                    self.episodes = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load existing episode stats: {e}")
            self.episodes = []
    
    def log_episode(self, episode_num, drone_id, reward, exploration, states, timestamp=None):
        """Log an episode completion with statistics."""
        if timestamp is None:
            timestamp = datetime.now().isoformat()
        
        episode_data = {
            "episode": episode_num,
            "drone_id": drone_id,
            "reward": reward,
            "exploration": exploration,
            "states": states,
            "timestamp": timestamp
        }
        
        self.episodes.append(episode_data)
        self._save()
        return episode_data
    
    def _save(self):
        """Persist episodes to disk."""
        try:
            with open(self.log_file, 'w') as f:
                json.dump(self.episodes, f, indent=2)
        except Exception as e:
            print(f"Error saving episode stats: {e}")
    
    def get_episode(self, episode_num, drone_id=None):
        """Retrieve episode data by number and optional drone_id."""
        results = [ep for ep in self.episodes if ep["episode"] == episode_num]
        if drone_id is not None:
            results = [ep for ep in results if ep["drone_id"] == drone_id]
        return results
    
    def get_drone_history(self, drone_id):
        """Get all episodes for a specific drone."""
        return [ep for ep in self.episodes if ep["drone_id"] == drone_id]
    
    def get_recent(self, limit=10):
        """Get the most recent N episodes."""
        return self.episodes[-limit:] if self.episodes else []
    
    def summary_stats(self):
        """Return summary statistics across all episodes."""
        if not self.episodes:
            return {}
        
        total_reward = sum(ep["reward"] for ep in self.episodes)
        avg_reward = total_reward / len(self.episodes)
        max_reward = max(ep["reward"] for ep in self.episodes)
        min_reward = min(ep["reward"] for ep in self.episodes)
        
        avg_exploration = sum(ep["exploration"] for ep in self.episodes) / len(self.episodes)
        avg_states = sum(ep["states"] for ep in self.episodes) / len(self.episodes)
        
        return {
            "total_episodes": len(self.episodes),
            "total_reward": total_reward,
            "avg_reward": avg_reward,
            "max_reward": max_reward,
            "min_reward": min_reward,
            "avg_exploration": avg_exploration,
            "avg_states": avg_states
        }
