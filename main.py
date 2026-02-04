import pygame
import math
from noise import pnoise1
import random
import configFiles.configM as cf
from elements.terrain import draw_terrain
from elements.drone import drone_draw
import controls.controlM as con
from events.mainE import main_event
pygame.init()
W,H=cf.W,cf.H
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Stacked Wavy Circles")
clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 16)
overlay = pygame.Surface((W, H), pygame.SRCALPHA)  # <-- SRCALPHA allows transparency

# transmitter=random.randint()
state ={
    'running': True,
    'tower_connection': False,
    'selected_drone':0
}
running = True
while state["running"]:
    clock.tick(60)
    main_event(state)
    screen.fill((20, 20, 20))
    draw_terrain(screen,font,overlay,tower_connection=state['tower_connection'])
    drone_draw(screen,font,overlay,state['selected_drone'] % cf.number_of_drone)
    pygame.display.flip()

pygame.quit()
