import pygame
import random
import configFiles.configM as cf
def drone_draw(screen):
    pygame.draw.rect(screen,(100,100,100),(cf.drone_x,cf.drone_y,10,10)) 