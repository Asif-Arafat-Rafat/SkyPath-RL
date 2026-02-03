from configFiles.terrain_config import configT
from configFiles.disp_config import disp_settings
from configFiles.drone_config import drone_config
W,H,number_of_drone=disp_settings()
hills,LAYERS,CENTERS,BASE_RADIUS,LAYER_GAP,NOISE_FREQ,NOISE_AMP,transmitter_tower_height,receiver_tower_height= configT(W,H)
drone_x = []
drone_y = []
drone_z = []
drone_speed = []
drone_range = []

for n in range(number_of_drone):
    x, y, z, speed, range_ = drone_config(n)

    drone_x.append(x)
    drone_y.append(y)
    drone_z.append(z)
    drone_speed.append(speed)
    drone_range.append(range_)

