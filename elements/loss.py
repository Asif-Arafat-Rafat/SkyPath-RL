import math
import random

def free_space_path_loss(distance_m, freq_mhz):
    return 20 * math.log10(distance_m) + 20 * math.log10(freq_mhz) - 27.56


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

    C = 3e8
    total_dist = math.dist(tx, rx)
    wavelength = C / freq_hz

    total_loss = 0

    for hill in hills:
        # Midpoint of hill segment (approx knife-edge)
        (x1, y1), (x2, y2) = hill["segment"]
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        hill_height = hill["height"]

        # Linear interpolation to find LOS height at hill midpoint
        t = math.dist(tx[:2], (mid_x, mid_y)) / total_dist
        los_height = tx[2] + t * (rx[2] - tx[2])

        # How much hill intrudes above LOS
        h = hill_height - los_height
        if h <= 0:
            continue  # below LOS → negligible loss

        # Hill width penalty (sublinear)
        hill_width = math.dist((x1, y1), (x2, y2))
        width_factor = math.log1p(hill_width)  # log(1 + width)

        # Fresnel-normalized intrusion
        fresnel = math.sqrt(wavelength * total_dist / 2)
        norm_h = h / (fresnel + 1e-6)  # prevent division by zero

        # Smooth diffraction loss
        hill_loss = 20 * math.log10(1 + norm_h * width_factor)

        # Accumulate loss from all hills
        total_loss += hill_loss

    return total_loss

def add_fading(power_dbm):
    fading = random.gauss(0, 2)  # shadow fading
    return power_dbm + fading
