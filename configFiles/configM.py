from configFiles.terrain_config import configT
from configFiles.disp_config import disp_settings
from configFiles.drone_config import drone_config
W,H=disp_settings()
hills,LAYERS,CENTERS,BASE_RADIUS,LAYER_GAP,NOISE_FREQ,NOISE_AMP= configT(W,H)
drone_x,drone_y,drone_z,speed,range=drone_config()