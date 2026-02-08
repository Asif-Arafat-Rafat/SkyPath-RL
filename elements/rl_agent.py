"""
Reinforcement Learning agent for drone signal relay optimization
Uses Q-learning with continuous state space and discrete action space
"""
import numpy as np
import math
from collections import defaultdict
import configFiles.configM as cf

class DroneRLAgent:
    def __init__(self, grid_size=20, height_levels=5, learning_rate=0.1, discount_factor=0.95, 
            epsilon_start=0.3, epsilon_min=0.05, epsilon_decay=0.995):
        """
        Initialize RL agent for drone positioning in 3D space
        
        grid_size: size of discretized position grid (x, y)
        height_levels: number of discretized altitude levels
        learning_rate: alpha parameter for Q-learning updates
        discount_factor: gamma parameter for future rewards
        epsilon_start: initial exploration rate
        epsilon_min: minimum exploration rate
        epsilon_decay: exploration decay rate per episode
        """
        self.grid_size = grid_size
        self.height_levels = height_levels
        self.learning_rate = learning_rate
        self.discount_factor = discount_factor
        self.epsilon = epsilon_start
        self.epsilon_min = epsilon_min
        self.epsilon_decay = epsilon_decay
        
        # Q-table: state -> {action: q_value}
        # 3D state: (grid_x, grid_y, height_level)
        self.q_table = defaultdict(lambda: {i: 0.0 for i in range(10)})
        
        # 10 discrete actions: 8 horizontal directions + up + down
        # 0-7: N, NE, E, SE, S, SW, W, NW (horizontal movement)
        # 8: UP (increase altitude)
        # 9: DOWN (decrease altitude)
        self.actions = [
            (0, -1, 0),      # N (up on screen)
            (1, -1, 0),      # NE
            (1, 0, 0),       # E (right)
            (1, 1, 0),       # SE
            (0, 1, 0),       # S (down on screen)
            (-1, 1, 0),      # SW
            (-1, 0, 0),      # W (left)
            (-1, -1, 0),     # NW
            (0, 0, 1),       # UP (increase altitude)
            (0, 0, -1),      # DOWN (decrease altitude)
        ]
        
        self.step_count = 0
        self.episode_count = 0
        self.learning_history = []
        
    def discretize_position(self, pos_3d, bounds, height_bounds):
        """Convert continuous 3D position to discrete grid state
        
        pos_3d: (x, y, z) position
        bounds: (min_x, max_x, min_y, max_y)
        height_bounds: (min_z, max_z)
        """
        x, y, z = pos_3d
        min_x, max_x, min_y, max_y = bounds
        min_z, max_z = height_bounds
        
        # Discretize horizontal position
        grid_x = int((x - min_x) / (max_x - min_x) * (self.grid_size - 1))
        grid_y = int((y - min_y) / (max_y - min_y) * (self.grid_size - 1))
        
        # Discretize altitude
        grid_z = int((z - min_z) / (max_z - min_z) * (self.height_levels - 1))
        
        # Clamp to valid range
        grid_x = max(0, min(grid_x, self.grid_size - 1))
        grid_y = max(0, min(grid_y, self.grid_size - 1))
        grid_z = max(0, min(grid_z, self.height_levels - 1))
        
        return (grid_x, grid_y, grid_z)
    
    def continuous_from_grid(self, grid_pos, bounds, height_bounds):
        """Convert grid position back to continuous 3D coordinates
        
        grid_pos: (grid_x, grid_y, grid_z)
        bounds: (min_x, max_x, min_y, max_y)
        height_bounds: (min_z, max_z)
        """
        grid_x, grid_y, grid_z = grid_pos
        min_x, max_x, min_y, max_y = bounds
        min_z, max_z = height_bounds
        
        x = min_x + (grid_x / (self.grid_size - 1)) * (max_x - min_x)
        y = min_y + (grid_y / (self.grid_size - 1)) * (max_y - min_y)
        z = min_z + (grid_z / (self.height_levels - 1)) * (max_z - min_z)
        
        return (x, y, z)
    
    def select_action(self, state, training=True):
        """
        Select action using epsilon-greedy strategy
        
        state: discrete grid position tuple
        training: if True, use exploration; if False, use greedy
        
        Returns: action index
        """
        try:
            # Ensure state is valid
            if not isinstance(state, tuple) or len(state) != 3:
                return np.random.randint(0, len(self.actions))
            
            # Ensure state exists in q_table
            if state not in self.q_table:
                self.q_table[state] = {i: 0.0 for i in range(10)}
            
            if training and np.random.random() < self.epsilon:
                # Explore: random action
                return np.random.randint(0, len(self.actions))
            else:
                # Exploit: best action from Q-table
                q_values = self.q_table[state]
                if not q_values:
                    return np.random.randint(0, len(self.actions))
                max_q = max(q_values.values())
                best_actions = [a for a, q in q_values.items() if q == max_q]
                return np.random.choice(best_actions)
        except Exception as e:
            print(f"Error selecting action: {e}")
            return np.random.randint(0, len(self.actions))
    
    def apply_action(self, position, action_idx, bounds, height_bounds, step_size=10, height_step=5):
        """
        Apply action to drone position in 3D space
        
        position: current (x, y, z) position
        action_idx: index of action to apply
        bounds: (min_x, max_x, min_y, max_y)
        height_bounds: (min_z, max_z)
        step_size: pixels to move per step (horizontal)
        height_step: meters to move per step (vertical)
        
        Returns: new position
        """
        dx, dy, dz = self.actions[action_idx]
        new_x = position[0] + dx * step_size
        new_y = position[1] + dy * step_size
        new_z = position[2] + dz * height_step
        
        # Keep drone within bounds
        min_x, max_x, min_y, max_y = bounds
        min_z, max_z = height_bounds
        new_x = max(min_x, min(new_x, max_x))
        new_y = max(min_y, min(new_y, max_y))
        new_z = max(min_z, min(new_z, max_z))
        
        # Prevent drone from entering hills if its altitude is insufficient.
        # If the action is a horizontal move (dx or dy != 0) and the target
        # (new_x, new_y) lies within a hill whose height >= new_z, block the
        # horizontal movement and keep the drone at its previous (x,y). Vertical
        # moves (up/down) are still allowed so the agent can gain altitude.
        try:
            moving_horizontally = (dx != 0 or dy != 0)
            # iterate over known hill definitions; guard for mismatched lengths
            max_hills = min(len(cf.CENTERS), len(cf.BASE_RADIUS), len(cf.LAYERS))
            for h in range(max_hills):
                try:
                    cx, cy = cf.CENTERS[h]
                    radius = cf.BASE_RADIUS[h]
                    # hill elevation in meters (LAYERS[h] * scale as used elsewhere)
                    hill_height = cf.LAYERS[h] * getattr(cf, 'scale', 10)
                    dist_to_center = math.hypot(new_x - cx, new_y - cy)
                    if dist_to_center <= radius:
                        # inside hill footprint
                        if moving_horizontally and new_z <= hill_height:
                            # block horizontal move
                            new_x, new_y = position[0], position[1]
                            break
                except Exception:
                    # skip malformed hill entry
                    continue
        except Exception:
            pass

        return (new_x, new_y, new_z)
    
    def calculate_reward(self, rx_power_dbm_direct, rx_power_dbm_relay, 
                        tx_distance_direct, tx_distance_relay,
                        drone_height, avg_terrain_height,
                        threshold_good=-50, threshold_bad=-80):
        """
        Calculate reward based on signal quality improvement and height advantage
        
        rx_power_dbm_direct: received power via direct path in dBm
        rx_power_dbm_relay: received power via relay in dBm
        tx_distance_direct: total distance for direct path
        tx_distance_relay: total distance for relay path
        drone_height: current drone altitude
        avg_terrain_height: average terrain height (for LOS advantage)
        threshold_good: good signal level in dBm
        threshold_bad: bad signal level in dBm
        
        Returns: reward value
        """
        try:
            # Validate inputs
            if rx_power_dbm_direct is None or math.isnan(rx_power_dbm_direct) or math.isinf(rx_power_dbm_direct):
                rx_power_dbm_direct = -80.0
            if rx_power_dbm_relay is None or math.isnan(rx_power_dbm_relay) or math.isinf(rx_power_dbm_relay):
                rx_power_dbm_relay = -80.0
            if tx_distance_direct is None or tx_distance_direct <= 0:
                tx_distance_direct = 1000.0
            if tx_distance_relay is None or tx_distance_relay <= 0:
                tx_distance_relay = 1000.0
            if drone_height is None or math.isnan(drone_height) or math.isinf(drone_height):
                drone_height = 50.0
            if avg_terrain_height is None or math.isnan(avg_terrain_height) or math.isinf(avg_terrain_height):
                avg_terrain_height = 0.0
            
            # Base reward: improvement over direct path
            improvement = rx_power_dbm_relay - rx_power_dbm_direct
            reward = improvement * 0.5
            
            # Bonus for good signal quality
            if rx_power_dbm_relay > threshold_good:
                reward += 10.0
            elif rx_power_dbm_relay < threshold_bad:
                reward -= 5.0
            
            # Distance penalty: prefer shorter paths
            if tx_distance_relay < tx_distance_direct:
                reward += 2.0
            
            # Height advantage: reward for being above terrain (better LOS)
            height_above_terrain = drone_height - avg_terrain_height
            if height_above_terrain > 20:  # More than 20m above terrain
                reward += 3.0
            elif height_above_terrain < 10:  # Less than 10m above terrain
                reward -= 1.0
            
            # Ensure reward is valid
            if math.isnan(reward) or math.isinf(reward):
                reward = 0.0
            
            return reward
        except Exception as e:
            print(f"Error calculating reward: {e}")
            return 0.0
    
    def update_q_table(self, state, action, reward, next_state, done=False):
        """
        Update Q-table using Q-learning update rule
        
        Q(s,a) = Q(s,a) + α[r + γ*max(Q(s',a')) - Q(s,a)]
        """
        try:
            # Ensure state and action are valid types
            if not isinstance(state, tuple) or not isinstance(action, int):
                return 0
            
            # Ensure state exists in q_table
            if state not in self.q_table:
                self.q_table[state] = {i: 0.0 for i in range(10)}
            
            # Ensure action is in state's actions
            if action not in self.q_table[state]:
                self.q_table[state][action] = 0.0
            
            current_q = self.q_table[state][action]
            
            # Ensure next_state exists
            if next_state not in self.q_table:
                self.q_table[next_state] = {i: 0.0 for i in range(10)}
            
            # Get max Q value for next state
            next_q_values = self.q_table[next_state]
            max_next_q = max(next_q_values.values()) if next_q_values else 0
            
            # Q-learning update
            new_q = current_q + self.learning_rate * (reward + self.discount_factor * max_next_q - current_q)
            self.q_table[state][action] = new_q
            
            return new_q
        except Exception as e:
            print(f"Error updating Q-table: {e}")
            return 0
    
    def step(self, position, bounds, height_bounds, signal_metrics, terrain_info, training=True):
        """
        Execute one step of learning in 3D space
        
        position: current drone position (x, y, z)
        bounds: (min_x, max_x, min_y, max_y)
        height_bounds: (min_z, max_z)
        signal_metrics: dict with keys:
            - rx_power_dbm_direct: received power direct path
            - rx_power_dbm_relay: received power relay path
            - tx_distance_direct: distance direct path
            - tx_distance_relay: distance relay path
        terrain_info: dict with terrain information:
            - avg_height: average terrain height
        training: whether to update Q-table
        
        Returns: new position, action taken, reward
        """
        # Discretize state (3D)
        state = self.discretize_position(position, bounds, height_bounds)
        
        # Select action
        action = self.select_action(state, training=training)
        
        # Apply action to get new position
        new_position = self.apply_action(position, action, bounds, height_bounds)
        new_state = self.discretize_position(new_position, bounds, height_bounds)
        
        # Calculate reward based on current metrics and height
        reward = self.calculate_reward(
            signal_metrics["rx_power_dbm_direct"],
            signal_metrics["rx_power_dbm_relay"],
            signal_metrics["tx_distance_direct"],
            signal_metrics["tx_distance_relay"],
            new_position[2],  # drone height
            terrain_info.get("avg_height", 0)
        )
        
        # Update Q-table if training
        if training:
            self.update_q_table(state, action, reward, new_state)
        
        # Update step counter
        self.step_count += 1
        
        return new_position, action, reward
    
    def end_episode(self):
        """Call at end of episode to decay epsilon"""
        self.epsilon = max(self.epsilon_min, self.epsilon * self.epsilon_decay)
        self.episode_count += 1
        self.learning_history.append(self.epsilon)
    
    def get_learning_stats(self):
        """Return learning statistics"""
        return {
            "step_count": self.step_count,
            "episode_count": self.episode_count,
            "epsilon": self.epsilon,
            "q_table_size": len(self.q_table)
        }
    
    def save_policy(self, filepath):
        """Save learned Q-table to file"""
        import json
        
        # Convert defaultdict to regular dict for JSON serialization
        q_table_serializable = {}
        for state, actions in self.q_table.items():
            q_table_serializable[str(state)] = actions
        
        policy = {
            "q_table": q_table_serializable,
            "epsilon": self.epsilon,
            "step_count": self.step_count,
            "episode_count": self.episode_count
        }
        
        try:
            with open(filepath, 'w') as f:
                json.dump(policy, f, indent=2)
            print(f"Policy saved to {filepath}")
        except Exception as e:
            print(f"Error saving policy: {e}")
    
    def load_policy(self, filepath):
        """Load learned Q-table from file"""
        import json
        import ast
        
        try:
            with open(filepath, 'r') as f:
                policy = json.load(f)
            
            # Restore Q-table - convert string keys back to tuples
            self.q_table = defaultdict(lambda: {i: 0.0 for i in range(10)})
            for state_str, actions in policy["q_table"].items():
                try:
                    # Safely convert string representation of tuple to actual tuple
                    state = ast.literal_eval(state_str)
                    # Ensure actions is a proper dict with all action keys
                    action_dict = {i: 0.0 for i in range(10)}
                    if isinstance(actions, dict):
                        for action_key, q_val in actions.items():
                            try:
                                action_idx = int(action_key)
                                action_dict[action_idx] = float(q_val)
                            except (ValueError, TypeError):
                                pass
                    self.q_table[state] = action_dict
                except Exception:
                    # Skip malformed entries
                    continue
            
            self.epsilon = policy.get("epsilon", self.epsilon)
            self.step_count = policy.get("step_count", 0)
            self.episode_count = policy.get("episode_count", 0)
            print(f"Policy loaded from {filepath}")
        except Exception as e:
            print(f"Error loading policy: {e}")
