
import pygame
import math
from noise import pnoise1
import configFiles.configM as cf
import random
shown=0
inter=[]
hill=cf.hills
inter_points = [[] for _ in range(hill)]

def line_of_sight_validation(x, y):
    return abs(y - (35 + 530/730*(x - 35))) < cf.tolerance

def draw_terrain(screen,font,overlay,tower_connection=False):
    global  inter, shown, inter_points
    W,H,hills,LAYERS,CENTERS,BASE_RADIUS,LAYER_GAP,NOISE_FREQ,NOISE_AMP,transmitter_tower_height,receiver_tower_height,distance=cf.W,cf.H,cf.hills,cf.LAYERS,cf.CENTERS,cf.BASE_RADIUS,cf.LAYER_GAP,cf.NOISE_FREQ,cf.NOISE_AMP,cf.transmitter_tower_height,cf.receiver_tower_height,cf.distance
    pygame.draw.rect(screen,(0,200,0),(25,25,20,20),10)
    text_surface=font.render(str(f"T:{transmitter_tower_height}m"),True,(255,255,255))
    text_rect = text_surface.get_rect(center=(35,35))
    screen.blit(text_surface, text_rect)
    pygame.draw.rect(screen,(0,0,200),(W-45,H-45,20,20),10)
    text_surface=font.render(str(f"R:{receiver_tower_height}m"),True,(255,255,255))
    text_rect = text_surface.get_rect(center=(W-35,H-35))
    screen.blit(text_surface, text_rect)
    text_surface=font.render(str(f"Distance between towers: {cf.distance}"),True,(255,255,255))
    text_rect = text_surface.get_rect(center=(200,H-10))
    screen.blit(text_surface, text_rect)
    text_surface=font.render(str(f"tolerance: {cf.tolerance}"),True,(255,255,255))
    text_rect = text_surface.get_rect(center=(500,H-10))
    screen.blit(text_surface, text_rect)
    if( tower_connection):
        pygame.draw.line(screen,(255,255,0),(35,35),(W-35,H-35),2)
    # ---- DRAW FROM OUTER TO INNER ----
    for h in range(hills):
        if h==1 or h==0:
            continue
        text_surface=font.render(str(f"{LAYERS[h]*10}m"),True,(255,255,255))
        text_rect = text_surface.get_rect(center=(CENTERS[h][0],CENTERS[h][1]))
        screen.blit(text_surface, text_rect)
        for layer in range(LAYERS[h]):
            radius = BASE_RADIUS[h] - layer * LAYER_GAP[h]
            points = []

            for i in range(360):
                theta = math.radians(i)

                n = pnoise1(i * NOISE_FREQ[h] + layer * 10)
                r = radius + n * NOISE_AMP[h]

                x = CENTERS[h][0] + r * math.cos(theta)
                y = CENTERS[h][1] + r * math.sin(theta)
                if not cf.los:
                    if line_of_sight_validation(x,y):
                        p_x=int(x)
                        p_y=int(y)
                        if (x,y) in inter:
                            cf.los=True                        
                        else:
                            inter.append((x, y))
                            inter_points[h].append([p_x,p_y])
                            print("LOS blocked at:",x,y)
                points.append((x, y))
            for i in range(len(inter_points[h])):
                pygame.draw.circle(screen,(225,55*27*int(h+i)%256,0),inter_points[h][i],2)
            color = (0, 200 - layer/10 * 20, 255)
            pygame.draw.polygon(screen, color, points, 2)



            color = (0, 200 - layer/10 * 20, 255)
            pygame.draw.polygon(screen, color, points, 2)
    if shown == 0:
        print(f"inter_points: {inter_points}")
        shown = 1
