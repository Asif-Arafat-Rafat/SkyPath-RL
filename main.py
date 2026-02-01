import pygame
import math
from noise import pnoise1
import random
import configFiles.configM as cf
from elements.terrain import draw_terrain
from elements.drone import drone_draw
pygame.init()
W,H=cf.W,cf.H
screen = pygame.display.set_mode((W, H))
pygame.display.set_caption("Stacked Wavy Circles")
clock = pygame.time.Clock()
font = pygame.font.SysFont("arial", 16)
overlay = pygame.Surface((W, H), pygame.SRCALPHA)  # <-- SRCALPHA allows transparency

# transmitter=random.randint()

running = True
while running:
    clock.tick(60)
    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

    screen.fill((20, 20, 20))

    draw_terrain(screen,font)
    drone_draw(screen)

    pygame.display.flip()

pygame.quit()
