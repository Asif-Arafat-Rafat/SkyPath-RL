import pygame
import configFiles.configM as cf
def main_event(state):
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            state["running"]=False
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                state["running"]=False
            if event.key == pygame.K_v:
                state['tower_connection']=not state['tower_connection']
            if event.key == pygame.K_TAB:
                state['selected_drone']+=1
            if event.key == pygame.K_UP:
                cf.drones[state['selected_drone']][1]-=cf.speed
            if event.key == pygame.K_DOWN:
                cf.drones[state['selected_drone']][1]+=cf.speed
            if event.key == pygame.K_LEFT:
                cf.drones[state['selected_drone']][0]-=cf.speed
            if event.key == pygame.K_RIGHT:
                cf.drones[state['selected_drone']][0]+=cf.speed
            if event.key == pygame.K_q:
                cf.drones[state['selected_drone']][2]+=cf.speed
            if event.key == pygame.K_e:
                cf.drones[state['selected_drone']][2]-=cf.speed
            if event.key == pygame.K_EQUALS:
                cf.tolerance+=0.5
                cf.los=False
            if event.key == pygame.K_MINUS:
                cf.tolerance-=0.5
                cf.los=False
                if cf.tolerance<0:
                    cf.tolerance=0
