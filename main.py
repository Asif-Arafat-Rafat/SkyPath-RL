import pygame
import math
import random
import configFiles.configM as cf
from configFiles.terrain_moderator import terrain_moderator, calculate_drone_relay_path_loss, get_drone_signal_metrics
from elements.drone_controller import DroneController, draw_drone_with_rl
from elements.signal_viz import SignalVisualizer
from elements.data_panel import DataPanel
from elements.chart_logger import ChartLogger
import controls.controlM as con
from events.mainE import main_event
pygame.init()
W, H = cf.W, cf.H

# Create signal visualization with larger height for dual path display
signal_viz = SignalVisualizer(width=400, height=600, offset_x=W, offset_y=0)

# Create data panel for metrics
data_panel = DataPanel(width=400, height=600, offset_x=W + 400, offset_y=0)

# Create chart logger
chart_logger = ChartLogger(log_dir="communication_logs")
chart_image_surf = None
chart_interval = 60  # frames between chart renders
chart_tick = 0

# Create a larger display to show terrain, signal, and data windows
display_width = W + signal_viz.width + data_panel.width
display_height = max(H, signal_viz.height)
main_display = pygame.display.set_mode((display_width, display_height))
pygame.display.set_caption("Drone Relay Optimization - Terrain & Signal Analysis")

# Create surfaces for terrain and signal
terrain_surface = pygame.Surface((W, H))
clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 16)
overlay = pygame.Surface((W, H), pygame.SRCALPHA)  # <-- SRCALPHA allows transparency

# Initialize RL Drone Controller with 3D bounds
drone_bounds = (50, W - 50, 50, H - 50)  # (min_x, max_x, min_y, max_y)
drone_height_bounds = (10, 200)  # (min_z, max_z) in meters
drone_controller = DroneController(
    num_drones=cf.number_of_drone,
    bounds=drone_bounds,
    height_bounds=drone_height_bounds,
    grid_size=15,
    height_levels=5
)

# Try to load existing policies so training can resume
try:
    drone_controller.load_policies("drone_rl_policies")
except Exception:
    pass

# Signal tracking
tx_power_dbm = 20  # 20 dBm transmitted power
current_path_loss = 0
current_drone_relay_loss = None

# RL training parameters
enable_rl_training = True
rl_update_frequency = 10  # Update drone position every N frames
frame_counter = 0
episode_length = 300  # frames per episode
episode_frame = 0
total_episodes = 0
autosave_episodes = 5  # save policies every N episodes
max_episode_history = 10  # keep X episodes for adaptive training decision
train_reward_threshold = 5.0  # if avg reward >= this, stop training that drone


# transmitter=random.randint()
state = {
    'running': True,
    'tower_connection': False,
    'selected_drone': 0
}

running = True
while state["running"]:
    clock.tick(60)
    main_event(state)
    
    # Draw terrain on terrain_surface
    terrain_surface.fill((20, 20, 20))
    result, distances, path_losses, terrain_info = terrain_moderator(terrain_surface, font, overlay, tower_connection=state['tower_connection'])
    
    # Draw drones with RL stats
    draw_drone_with_rl(terrain_surface, font, overlay, drone_controller, state['selected_drone'] % cf.number_of_drone)
    
    # Extract path loss from results
    if path_losses and len(path_losses) > 0:
        current_path_loss = path_losses[0].get("total", 80.0)
        if current_path_loss is None or math.isnan(current_path_loss) or math.isinf(current_path_loss):
            current_path_loss = 80.0
    else:
        current_path_loss = 80.0
    
    # RL Training: Update drone position and calculate rewards
    current_drone_relay_loss = None
    if enable_rl_training and cf.drones and len(cf.drones) > 0:
        # Transmitter and receiver positions (3D)
        tx = (35, 35, cf.transmitter_tower_height)
        rx = (W - 35, H - 35, cf.receiver_tower_height)

        # Reconstruct hills_data (simplified - use empty list)
        hills_data = []
        freq_hz = 2.4e9

        # Gather per-drone signal metrics
        per_drone_metrics = []
        best_relay_loss = None
        for i in range(cf.number_of_drone):
            try:
                drone_pos_i = cf.drones[i]
                metrics_i = get_drone_signal_metrics(
                    tx_power_dbm,
                    tx,
                    rx,
                    drone_pos_i,
                    hills_data,
                    freq_hz,
                    current_path_loss
                )
            except Exception as e:
                print(f"Error getting metrics for drone {i}: {e}")
                metrics_i = {
                    "rx_power_dbm_direct": -80.0,
                    "rx_power_dbm_relay": -80.0,
                    "tx_distance_direct": 1000.0,
                    "tx_distance_relay": 1000.0,
                    "relay_total_loss": 100.0
                }
            per_drone_metrics.append(metrics_i)
            try:
                rl = metrics_i.get("relay_total_loss", None)
                if rl is not None:
                    if best_relay_loss is None or rl < best_relay_loss:
                        best_relay_loss = rl
            except Exception:
                pass

        current_drone_relay_loss = best_relay_loss

        # Decide per-drone training flags based on recent episode rewards
        training_flags = [enable_rl_training] * cf.number_of_drone
        try:
            for i in range(cf.number_of_drone):
                recent = drone_controller.episode_rewards[i][-max_episode_history:]
                if recent:
                    avg_recent = sum(recent) / len(recent)
                    # If performance is already good, stop training that drone
                    training_flags[i] = False if avg_recent >= train_reward_threshold else True
        except Exception:
            pass

        # Update drone positions every rl_update_frequency frames (all drones)
        frame_counter += 1
        if frame_counter >= rl_update_frequency:
            frame_counter = 0
            for i in range(cf.number_of_drone):
                try:
                    metrics_i = per_drone_metrics[i]
                    new_pos, action, reward = drone_controller.update_drone_position(
                        i,
                        metrics_i,
                        terrain_info,
                        training=training_flags[i]
                    )
                except Exception as e:
                    print(f"Error updating drone {i}: {e}")
        
        # Check if episode is complete
        episode_frame += 1
        if episode_frame >= episode_length:
            episode_frame = 0
            total_episodes += 1
            drone_controller.end_episode()
            
            # Save charts and data
            chart_logger.save_and_plot(filename_prefix=f"episode_{total_episodes}")
            chart_logger.reset()
            
            # Print episode statistics
            stats = drone_controller.get_episode_stats()
            # Autosave policies periodically
            if total_episodes % autosave_episodes == 0:
                try:
                    drone_controller.save_policies("drone_rl_policies")
                except Exception as e:
                    print(f"Error autosaving policies: {e}")

            # Print stats for selected drone
            selected_drone_idx = state['selected_drone'] % cf.number_of_drone
            selected_stats = stats.get(f"drone_{selected_drone_idx}", {})
            print(f"Episode {total_episodes} Complete - Drone {selected_drone_idx}: "
                  f"Reward={selected_stats.get('episode_reward', 0):.1f}, "
                  f"Exploration={selected_stats.get('epsilon', 0):.3f}, "
                  f"States={selected_stats.get('q_table_size', 0)}")
    
    # Fill main display with background
    main_display.fill((20, 20, 20))
    
    # Blit terrain surface to main display
    main_display.blit(terrain_surface, (0, 0))
    
    # Draw signal visualization on main display with both direct and relay paths
    signal_viz.draw_signal_visualization(main_display, tx_power_dbm, current_path_loss, current_drone_relay_loss)
    signal_viz.update()
    
    # Draw data panel with clear metrics comparison
    data_panel.draw_data_comparison(main_display, tx_power_dbm, current_path_loss, current_drone_relay_loss, cf.drones)
    
    # Log communication data for chart (per drone) and periodically render latest chart
    if enable_rl_training and cf.drones and len(cf.drones) > 0:
        chart_tick += 1
        for i in range(cf.number_of_drone):
            try:
                relay_loss_i = None
                # use previously computed per_drone_metrics if available
                if 'per_drone_metrics' in locals() and len(per_drone_metrics) > i:
                    relay_loss_i = per_drone_metrics[i].get('relay_total_loss')
                chart_logger.log_communication(
                    frame_num=episode_frame,
                    direct_loss=current_path_loss,
                    relay_loss=relay_loss_i,
                    tx_power=tx_power_dbm,
                    drone_alt=cf.drones[i][2],
                    episode=total_episodes
                )
            except Exception:
                continue

        # Render latest chart image periodically (to display in UI)
        if chart_tick >= chart_interval:
            chart_tick = 0
            try:
                chart_path = chart_logger.render_latest_chart()
                if chart_path:
                    try:
                        chart_image_surf = pygame.image.load(chart_path).convert()
                    except Exception as e:
                        print(f"Error loading chart image: {e}")
            except Exception as e:
                print(f"Error rendering latest chart: {e}")

        # Blit chart image if available
        if chart_image_surf:
            try:
                # scale to fit signal panel width
                chart_w = signal_viz.width
                chart_h = min(signal_viz.height // 2, chart_image_surf.get_height())
                scaled = pygame.transform.smoothscale(chart_image_surf, (chart_w, chart_h))
                main_display.blit(scaled, (W, 0))
            except Exception:
                pass
    
    # Draw training status
    if enable_rl_training:
        training_text = font.render(f"RL Training Active | Frame: {episode_frame}/{episode_length} | Episode: {total_episodes}", True, (100, 255, 100))
        main_display.blit(training_text, (W + 10, H - 30))
    
    pygame.display.flip()

# Save learned policies on exit
if enable_rl_training:
    drone_controller.save_policies("drone_rl_policies")

pygame.quit()
