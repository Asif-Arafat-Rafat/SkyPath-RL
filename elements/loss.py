import math
import random

def free_space_path_loss(distance_m, freq_mhz):
    """Calculate free space path loss"""
    try:
        # Validate inputs
        if distance_m is None or distance_m <= 0:
            distance_m = 1.0  # Minimum distance
        if freq_mhz is None or freq_mhz <= 0:
            freq_mhz = 2400.0  # Default 2.4 GHz
        
        fspl = 20 * math.log10(distance_m) + 20 * math.log10(freq_mhz) - 27.56
        
        # Validate result
        if math.isnan(fspl) or math.isinf(fspl):
            fspl = 70.0
        
        return fspl
    except Exception as e:
        print(f"Error calculating free space path loss: {e}")
        return 70.0


def rl_multi_hill_diffraction(tx, rx, hills, freq_hz):
    """
    tx, rx -> (x, y, z) in meters
    hills -> list of dicts, each hill:
             {
                "segment": [(x_start, y_start), (x_end, y_end)],
                "height": z_height
             }
    freq_hz -> frequency in Hz
    Returns: approximate diffraction loss in dB
    """
    try:
        # Validate inputs
        if tx is None or len(tx) < 3:
            return 0.0
        if rx is None or len(rx) < 3:
            return 0.0
        if freq_hz is None or freq_hz <= 0:
            freq_hz = 2.4e9
        if hills is None or len(hills) == 0:
            return 0.0

        C = 3e8
        total_dist = math.dist(tx, rx)
        
        # Avoid division by zero
        if total_dist <= 0:
            total_dist = 1.0
        
        wavelength = C / freq_hz

        total_loss = 0

        for hill in hills:
            try:
                # Midpoint of hill segment (approx knife-edge)
                segment = hill.get("segment")
                if segment is None or len(segment) < 2:
                    continue
                
                (x1, y1), (x2, y2) = segment
                mid_x = (x1 + x2) / 2
                mid_y = (y1 + y2) / 2
                hill_height = hill.get("height", 0)
                
                # Validate hill data
                if hill_height is None or math.isnan(hill_height):
                    hill_height = 0
                
                # Linear interpolation to find LOS height at hill midpoint
                dist_to_mid = math.dist(tx[:2], (mid_x, mid_y))
                if dist_to_mid <= 0:
                    t = 0.5
                else:
                    t = dist_to_mid / total_dist
                    t = max(0, min(t, 1.0))  # Clamp to [0, 1]
                
                los_height = tx[2] + t * (rx[2] - tx[2])

                # How much hill intrudes above LOS
                h = hill_height - los_height
                if h <= 0:
                    continue  # below LOS → negligible loss

                # Hill width penalty (sublinear)
                hill_width = math.dist((x1, y1), (x2, y2))
                if hill_width <= 0:
                    hill_width = 1.0
                    
                width_factor = math.log1p(hill_width)  # log(1 + width)

                # Fresnel-normalized intrusion
                fresnel = math.sqrt(abs(wavelength * total_dist / 2))
                if fresnel <= 0:
                    fresnel = 1e-6
                
                norm_h = h / (fresnel + 1e-6)  # prevent division by zero

                # Smooth diffraction loss
                hill_loss = 20 * math.log10(1 + norm_h * width_factor)
                
                # Validate hill loss
                if math.isnan(hill_loss) or math.isinf(hill_loss):
                    hill_loss = 0.0

                # Accumulate loss from all hills
                total_loss += hill_loss
                
            except Exception as e:
                print(f"Error processing hill in diffraction: {e}")
                continue

        # Validate total loss
        if math.isnan(total_loss) or math.isinf(total_loss):
            total_loss = 0.0
        
        return total_loss
        
    except Exception as e:
        print(f"Error calculating diffraction loss: {e}")
        return 0.0


def add_fading(power_dbm):
    """Add shadow fading to power signal"""
    try:
        if power_dbm is None or math.isnan(power_dbm) or math.isinf(power_dbm):
            power_dbm = 0.0
        
        fading = random.gauss(0, 2)  # shadow fading
        
        result = power_dbm + fading
        
        # Validate result
        if math.isnan(result) or math.isinf(result):
            result = 0.0
        
        return result
    except Exception as e:
        print(f"Error adding fading: {e}")
        return 0.0

