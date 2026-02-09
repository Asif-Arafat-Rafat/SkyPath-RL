"""
Upgrade Tracker
Keeps track of generated charts/images and exposes the latest path for UI panels.
"""
import os
import json

class UpgradeTracker:
    def __init__(self, store_file="communication_logs/upgrade_index.json"):
        self.store_file = store_file
        self.latest = None
        self.history = []
        # ensure directory exists
        d = os.path.dirname(store_file)
        if d and not os.path.exists(d):
            os.makedirs(d, exist_ok=True)
        # load existing index if present
        try:
            if os.path.exists(self.store_file):
                with open(self.store_file, 'r') as f:
                    data = json.load(f)
                    self.latest = data.get('latest')
                    self.history = data.get('history', [])
        except Exception:
            self.latest = None
            self.history = []

    def register(self, img_path):
        """Register a new chart/image path."""
        if img_path and os.path.exists(img_path):
            self.latest = img_path
            self.history.append({'path': img_path})
            # persist
            try:
                with open(self.store_file, 'w') as f:
                    json.dump({'latest': self.latest, 'history': self.history}, f)
            except Exception:
                pass

    def get_latest(self):
        return self.latest

    def get_history(self):
        return list(self.history)
