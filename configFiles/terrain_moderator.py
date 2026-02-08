from elements.terrain import draw_terrain
from elements.distance import calculate_distance
from elements.loss import rl_multi_hill_diffraction, free_space_path_loss, add_fading
import configFiles.configM as cf
import math
import pygame
once = False

def calculate_segment_loss(pos_from, pos_to, hills_data, freq_hz):
    """
    Calculate path loss for a single segment between two positions
    Includes both free-space path loss and knife-edge diffraction
    
    Returns: dict with fspl, diffraction, and total loss
    """
    try:
        distance = calculate_distance(pos_from, pos_to)
        if distance <= 0:
            distance = 1.0
        
        # Free-space path loss
        fspl = free_space_path_loss(distance, freq_hz / 1e6)
        if math.isnan(fspl) or math.isinf(fspl):
            fspl = 50.0
        
        # Knife-edge diffraction loss
        diffraction = rl_multi_hill_diffraction(pos_from, pos_to, hills_data, freq_hz)
        if math.isnan(diffraction) or math.isinf(diffraction):
            diffraction = 0.0
        
        total = fspl + diffraction
        if math.isnan(total) or math.isinf(total) or total < 0:
            total = 80.0
        
        return {
            "distance": distance,
            "fspl": fspl,
            "diffraction": diffraction,
            "total": total
        }
    except Exception:
        return {
            "distance": 1000.0,
            "fspl": 50.0,
            "diffraction": 0.0,
            "total": 80.0
        }

def calculate_multihop_relay_loss(tx_pos, drone_positions, rx_pos, hills_data, freq_hz):
    """
    Calculate path loss for multi-hop relay: TX → R0 → R1 → R2 → ... → RN → RX
    Each segment includes free-space path loss and knife-edge diffraction
    
    tx_pos: (x, y, z) transmitter position
    drone_positions: list of (x, y, z) drone positions in relay order
    rx_pos: (x, y, z) receiver position
    hills_data: list of hill dictionaries
    freq_hz: frequency in Hz
    
    Returns: dict with segment losses and total loss
    """
    try:
        segment_losses = []
        total_loss = 0.0
        
        # Build the complete relay path
        relay_path = [tx_pos] + drone_positions + [rx_pos]
        
        # Calculate loss for each segment
        for i in range(len(relay_path) - 1):
            segment_loss = calculate_segment_loss(relay_path[i], relay_path[i+1], hills_data, freq_hz)
            segment_losses.append(segment_loss)
            total_loss += segment_loss["total"]
        
        # Ensure total loss is valid
        if math.isnan(total_loss) or math.isinf(total_loss) or total_loss < 0:
            total_loss = 100.0
        
        return {
            "segment_losses": segment_losses,
            "total_loss": total_loss,
            "num_hops": len(relay_path) - 1,
            "relay_path": relay_path
        }
    except Exception as e:
        print(f"Error calculating multi-hop relay loss: {e}")
        return {
            "segment_losses": [],
            "total_loss": 100.0,
            "num_hops": 0,
            "relay_path": []
        }

def calculate_drone_relay_path_loss(tx_pos, drone_pos, rx_pos, hills_data, freq_hz):
    """
    Calculate path loss for TX → Drone → RX relay communication
    DEPRECATED: Use calculate_multihop_relay_loss instead
    Kept for backwards compatibility
    
    tx_pos: (x, y, z) transmitter position
    drone_pos: (x, y, z) drone position  
    rx_pos: (x, y, z) receiver position
    hills_data: list of hill dictionaries
    freq_hz: frequency in Hz
    
    Returns: total path loss in dB
    """
    try:
        # Use multi-hop function with single drone
        result = calculate_multihop_relay_loss(tx_pos, [drone_pos], rx_pos, hills_data, freq_hz)
        
        if result["num_hops"] >= 2:
            tx_drone_loss = result["segment_losses"][0]["total"]
            drone_rx_loss = result["segment_losses"][1]["total"]
        else:
            tx_drone_loss = 50.0
            drone_rx_loss = 50.0
        
        return {
            "tx_to_drone_loss": tx_drone_loss,
            "drone_to_rx_loss": drone_rx_loss,
            "total_loss": result["total_loss"],
            "tx_to_drone_dist": result["segment_losses"][0]["distance"] if result["segment_losses"] else 1000.0,
            "drone_to_rx_dist": result["segment_losses"][1]["distance"] if len(result["segment_losses"]) > 1 else 1000.0
        }
    except Exception as e:
        print(f"Error calculating drone relay path loss: {e}")
        return {
            "tx_to_drone_loss": 50.0,
            "drone_to_rx_loss": 50.0,
            "total_loss": 100.0,
            "tx_to_drone_dist": 1000.0,
            "drone_to_rx_dist": 1000.0
        }

def get_drone_signal_metrics(tx_power_dbm, tx_pos, rx_pos, drone_pos, hills_data, freq_hz, direct_path_loss):
    """
    Calculate signal metrics for multi-hop drone relay and return RL reward metrics
    
    Returns dict with signal quality information for RL agent
    """
    try:
        # Validate inputs
        if direct_path_loss is None or math.isnan(direct_path_loss) or math.isinf(direct_path_loss):
            direct_path_loss = 80.0
        
        # Get multi-hop relay path loss using all drones
        relay_info = calculate_multihop_relay_loss(tx_pos, cf.drones, rx_pos, hills_data, freq_hz)
        relay_total_loss = relay_info["total_loss"]
        
        # Calculate received powers
        rx_power_direct = tx_power_dbm - direct_path_loss
        rx_power_relay = tx_power_dbm - relay_total_loss
        
        # Validate power values
        if math.isnan(rx_power_direct) or math.isinf(rx_power_direct):
            rx_power_direct = -80.0
        if math.isnan(rx_power_relay) or math.isinf(rx_power_relay):
            rx_power_relay = -80.0
        
        # Calculate distances for direct path
        tx_rx_direct_dist = calculate_distance(tx_pos, rx_pos)
        if tx_rx_direct_dist <= 0:
            tx_rx_direct_dist = 1.0
        
        # Calculate total distance for relay path (sum of all segments)
        tx_relay_total_dist = 0.0
        if relay_info["segment_losses"]:
            for segment in relay_info["segment_losses"]:
                tx_relay_total_dist += segment["distance"]
        
        if tx_relay_total_dist <= 0:
            tx_relay_total_dist = 1.0
        
        return {
            "rx_power_dbm_direct": rx_power_direct,
            "rx_power_dbm_relay": rx_power_relay,
            "tx_distance_direct": tx_rx_direct_dist,
            "tx_distance_relay": tx_relay_total_dist,
            "relay_total_loss": relay_total_loss,
            "relay_info": relay_info  # Include detailed relay information
        }
    except Exception as e:
        print(f"Error calculating drone signal metrics: {e}")
        return {
            "rx_power_dbm_direct": -80.0,
            "rx_power_dbm_relay": -80.0,
            "tx_distance_direct": 1000.0,
            "tx_distance_relay": 1000.0,
            "relay_total_loss": 100.0
        }

def draw_multihop_relay_path(screen, relay_info):
    """
    Draw the multi-hop relay path on the screen
    Color code based on segment quality
    
    relay_info: dict from calculate_multihop_relay_loss with relay_path and segment_losses
    """
    try:
        if not relay_info or not relay_info.get("relay_path"):
            return
        
        relay_path = relay_info["relay_path"]
        segment_losses = relay_info.get("segment_losses", [])
        
        # Draw each segment with color based on loss quality
        for i in range(len(relay_path) - 1):
            pos_from = (int(relay_path[i][0]), int(relay_path[i][1]))
            pos_to = (int(relay_path[i+1][0]), int(relay_path[i+1][1]))
            
            # Get loss for this segment
            if i < len(segment_losses):
                segment_loss = segment_losses[i]["total"]
            else:
                segment_loss = 80.0
            
            # Map loss to color: Green (good ~50dB) to Red (bad ~100dB)
            loss_normalized = min(max((segment_loss - 50) / 50, 0), 1)  # Clamp to [0, 1]
            r = int(255 * loss_normalized)
            g = int(255 * (1 - loss_normalized))
            b = 100  # Add blue component for distinction from direct path
            color = (r, g, b)
            
            # Draw the segment line
            try:
                pygame.draw.line(screen, color, pos_from, pos_to, 2)
            except Exception:
                pass
            
            # Draw a small circle at intermediate nodes (drones)
            if i > 0 and i < len(relay_path) - 1:
                try:
                    pygame.draw.circle(screen, color, pos_to, 4)
                except Exception:
                    pass
    except Exception as e:
        print(f"Error drawing multi-hop relay path: {e}")

def terrain_moderator(screen,font,overlay,tower_connection=False):
    global once
    inter_points,visited,heights=draw_terrain(screen,font,overlay,tower_connection)
    lst=[sub for sub in inter_points if sub]
    result = [sub if len(sub) <= 2 else [sub[0], sub[-1]] for sub in lst]
    distances = []
    path_losses = []
    hills_data = []
    
    for i, sublist in enumerate(result):
        if len(sublist) == 2:
            dist = calculate_distance(sublist[0], sublist[1])
            distances.append(dist*cf.scale)
            
            # Build hill data for loss calculation
            if i in visited:
                height_idx = visited.index(i)
                hill_info = {
                    "segment": sublist,
                    "height": heights[height_idx]
                }
                hills_data.append(hill_info)
    
    # Calculate path loss with diffraction
    if hills_data and distances:
        try:
            # Transmitter and receiver positions (3D with height)
            tx = (35, 35, cf.transmitter_tower_height)
            rx = (cf.W - 35, cf.H - 35, cf.receiver_tower_height)
            
            # Convert frequency if needed (assuming it's in MHz, convert to Hz)
            freq_hz = 2.4e9  # 2.4 GHz default, adjust as needed
            
            # Calculate free space path loss
            fspl = free_space_path_loss(cf.distance, freq_hz / 1e6)
            
            # Validate FSPL
            if fspl is None or math.isnan(fspl) or math.isinf(fspl) or fspl < 0:
                fspl = 70.0
            
            # Calculate diffraction loss from hills
            diffraction_loss = rl_multi_hill_diffraction(tx, rx, hills_data, freq_hz)
            
            # Validate diffraction loss
            if diffraction_loss is None or math.isnan(diffraction_loss) or math.isinf(diffraction_loss):
                diffraction_loss = 0.0
            
            # Total path loss
            total_loss = fspl + diffraction_loss
            
            # Validate total loss
            if total_loss < 0 or math.isnan(total_loss) or math.isinf(total_loss):
                total_loss = 80.0
            
            # Add fading
            received_power = -total_loss + add_fading(0)
            
            # Validate received power
            if math.isnan(received_power) or math.isinf(received_power):
                received_power = -80.0
            
            if not once:
                print(f"inter_points: {inter_points}")
                print(f"heights: {[heights[f] for f in visited]}")
                print(f"Free Space Path Loss (FSPL): {fspl:.2f} dB")
                print(f"Diffraction Loss: {diffraction_loss:.2f} dB")
                print(f"Total Path Loss: {total_loss:.2f} dB")
                print(f"Received Power: {received_power:.2f} dBm")
                once = True
            
            path_losses.append({
                "fspl": fspl,
                "diffraction": diffraction_loss,
                "total": total_loss,
                "received_power": received_power
            })
        except Exception as e:
            print(f"Error in terrain_moderator path loss calculation: {e}")
            path_losses.append({
                "fspl": 70.0,
                "diffraction": 0.0,
                "total": 80.0,
                "received_power": -80.0
            })
    
    # Calculate average terrain height for RL agent
    try:
        if heights:
            avg_terrain_height = sum(heights) / len(heights)
            max_height = max(heights)
            min_height = min(heights)
        else:
            avg_terrain_height = 0
            max_height = 0
            min_height = 0
        
        # Validate values
        if math.isnan(avg_terrain_height) or math.isinf(avg_terrain_height) or avg_terrain_height < 0:
            avg_terrain_height = 0
        if math.isnan(max_height) or math.isinf(max_height) or max_height < 0:
            max_height = 0
        if math.isnan(min_height) or math.isinf(min_height) or min_height < 0:
            min_height = 0
            
    except Exception as e:
        print(f"Error calculating terrain height: {e}")
        avg_terrain_height = 0
        max_height = 0
        min_height = 0
    
    terrain_info = {
        "avg_height": avg_terrain_height,
        "max_height": max_height,
        "min_height": min_height
    }
    
    # Draw multi-hop relay path if tower_connection is enabled
    if tower_connection and cf.drones and len(cf.drones) > 0:
        try:
            tx = (35, 35, cf.transmitter_tower_height)
            rx = (cf.W - 35, cf.H - 35, cf.receiver_tower_height)
            freq_hz = 2.4e9
            
            # Calculate multi-hop relay loss for visualization
            relay_info = calculate_multihop_relay_loss(tx, cf.drones, rx, hills_data, freq_hz)
            
            # Draw the multi-hop relay path on screen
            draw_multihop_relay_path(screen, relay_info)
        except Exception as e:
            print(f"Error visualizing multi-hop relay: {e}")
    
    return result, distances, path_losses, terrain_info