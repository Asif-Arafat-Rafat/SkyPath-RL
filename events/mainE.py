import pygame

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