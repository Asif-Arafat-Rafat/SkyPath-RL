import pygame
import random
import configFiles.configM as cf
def drone_draw(screen, font, overlay):
    overlay.fill((0,0,0,0))  # <-- clear overlay each frame
    for i in range(cf.number_of_drone):
        text_surface=font.render(str(f"{cf.drone_z[i]}m"),True,(255,255,255))
        text_rect = text_surface.get_rect(center=(cf.drone_x[i], cf.drone_y[i]+20))
        screen.blit(text_surface, text_rect)
        pygame.draw.circle(screen, (255,100,100), (cf.drone_x[i], cf.drone_y[i]), 10)
        text_surface0=font.render(str(f"{i}"),True,(255,255,255))
        text_rect0 = text_surface0.get_rect(center=(cf.drone_x[i], cf.drone_y[i]))
        screen.blit(text_surface0, text_rect0)
        screen.blit(overlay, (0,0))
        pygame.draw.circle(overlay, (255,0,0,20), (cf.drone_x[i], cf.drone_y[i]), cf.drone_range[i])

