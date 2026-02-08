"""
Drone controller integrating RL agent for intelligent movement
"""
import pygame
import configFiles.configM as cf
from elements.rl_agent import DroneRLAgent

class DroneController:
    def __init__(self, num_drones, bounds, height_bounds, grid_size=20, height_levels=5):
        """
        Initialize drone controller with RL agents for 3D movement
        
        num_drones: number of drones to control
        bounds: (min_x, max_x, min_y, max_y) for horizontal movement area
        height_bounds: (min_z, max_z) for altitude bounds
        grid_size: size of RL horizontal grid
        height_levels: number of altitude levels
        """
        self.num_drones = num_drones
        self.bounds = bounds
        self.height_bounds = height_bounds
        self.agents = [DroneRLAgent(grid_size=grid_size, height_levels=height_levels) for _ in range(num_drones)]
        self.episode_rewards = [[] for _ in range(num_drones)]
        self.cumulative_rewards = [0 for _ in range(num_drones)]
        self.update_counter = 0
        self.update_frequency = 5  # Update position every N frames
        
    def update_drone_position(self, drone_idx, signal_metrics, terrain_info, training=True):
        """
        Update drone position using RL agent in 3D space
        
        drone_idx: index of drone to update
        signal_metrics: dict with signal quality metrics
        terrain_info: dict with terrain information (avg_height, etc)
        training: whether to train the agent
        
        Returns: new position, action, and reward
        """
        if drone_idx >= len(self.agents):
            return cf.drones[drone_idx], 0, 0
        
        agent = self.agents[drone_idx]
        current_pos = cf.drones[drone_idx]  # Get (x, y, z)
        
        # Execute RL step in 3D
        new_pos, action, reward = agent.step(
            current_pos, 
            self.bounds,
            self.height_bounds,
            signal_metrics,
            terrain_info,
            training=training
        )
        
        # Update drone position in config
        cf.drones[drone_idx] = new_pos
        
        # Track reward
        self.cumulative_rewards[drone_idx] += reward
        
        return new_pos, action, reward
    
    def end_episode(self):
        """End episode and decay exploration"""
        for i, agent in enumerate(self.agents):
            self.episode_rewards[i].append(self.cumulative_rewards[i])
            self.cumulative_rewards[i] = 0
            agent.end_episode()
    
    def get_episode_stats(self):
        """Get statistics for current episode"""
        stats = {}
        for i, agent in enumerate(self.agents):
            stats[f"drone_{i}"] = {
                "cumulative_reward": self.cumulative_rewards[i],
                "episode_reward": self.episode_rewards[i][-1] if self.episode_rewards[i] else 0,
                "q_table_size": len(agent.q_table),
                "epsilon": agent.epsilon
            }
        return stats
    
    def save_policies(self, base_filepath="drone_policies"):
        """Save all drone policies"""
        for i, agent in enumerate(self.agents):
            filepath = f"{base_filepath}_drone_{i}.json"
            agent.save_policy(filepath)
    
    def load_policies(self, base_filepath="drone_policies"):
        """Load all drone policies"""
        for i, agent in enumerate(self.agents):
            filepath = f"{base_filepath}_drone_{i}.json"
            agent.load_policy(filepath)

def draw_drone_with_rl(screen, font, overlay, controller, selected_drone=0):
    """
    Draw drones and their RL information including altitude
    
    screen: pygame surface to draw on
    font: pygame font object
    overlay: overlay surface for transparency effects
    controller: DroneController instance
    selected_drone: index of selected drone
    """
    overlay.fill((0, 0, 0, 0))  # Clear overlay
    
    for i in range(cf.number_of_drone):
        # Draw drone
        text_surface = font.render(str(f"{cf.drones[i][2]:.1f}m"), True, (255, 255, 255))
        text_rect = text_surface.get_rect(center=(cf.drones[i][0], cf.drones[i][1] + 20))
        screen.blit(text_surface, text_rect)
        
        color = (100, 255, 100) if i == selected_drone else (255, 100, 100)
        pygame.draw.circle(screen, color, (cf.drones[i][0], cf.drones[i][1]), 10)
        
        # Draw drone ID
        text_surface0 = font.render(str(f"{i}"), True, (255, 255, 255))
        text_rect0 = text_surface0.get_rect(center=(cf.drones[i][0], cf.drones[i][1]))
        screen.blit(text_surface0, text_rect0)
        
        # Draw drone range
        screen.blit(overlay, (0, 0))
        pygame.draw.circle(overlay, (255, 0, 0, 5), (cf.drones[i][0], cf.drones[i][1]), cf.drone_range[i])
        
        # Draw RL stats for selected drone
        if i == selected_drone and controller:
            agent = controller.agents[i]
            stats = controller.get_episode_stats()
            
            if f"drone_{i}" in stats:
                drone_stats = stats[f"drone_{i}"]
                y_offset = 40
                
                # Draw altitude
                text_surface = font.render(
                    f"Altitude: {cf.drones[i][2]:.1f}m", 
                    True, (100, 255, 255)
                )
                screen.blit(text_surface, (10, y_offset))
                
                # Draw epsilon (exploration rate)
                text_surface = font.render(
                    f"Exploration: {drone_stats['epsilon']:.3f}", 
                    True, (255, 255, 0)
                )
                screen.blit(text_surface, (10, y_offset + 20))
                
                # Draw cumulative reward
                text_surface = font.render(
                    f"Episode Reward: {drone_stats['episode_reward']:.1f}", 
                    True, (100, 255, 100)
                )
                screen.blit(text_surface, (10, y_offset + 40))
                
                # Draw Q-table size
                text_surface = font.render(
                    f"States Learned: {drone_stats['q_table_size']}", 
                    True, (100, 200, 255)
                )
                screen.blit(text_surface, (10, y_offset + 60))
