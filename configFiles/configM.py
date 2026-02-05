from configFiles.terrain_config import configT
from configFiles.disp_config import disp_settings
from configFiles.drone_config import drone_config
W,H,number_of_drone=disp_settings()
hills,LAYERS,CENTERS,BASE_RADIUS,LAYER_GAP,NOISE_FREQ,NOISE_AMP,transmitter_tower_height,receiver_tower_height,distance= configT(W,H)
drones=[]
drone_speed = []
drone_range = []
drones, speed, range_ = drone_config(number_of_drone)
drone_speed = [speed] * number_of_drone
drone_range = [range_] * number_of_drone
tolerance=1
los=False

