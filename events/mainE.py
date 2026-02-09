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
            # Data panel mode switching (1, 2, 3, 4)
            if event.key == pygame.K_1:
                state['data_mode'] = 1
                state['show_data_panel'] = True
                state['data_expanded'] = True
            if event.key == pygame.K_2:
                state['data_mode'] = 2
                state['show_data_panel'] = True
                state['data_expanded'] = True
            if event.key == pygame.K_3:
                state['data_mode'] = 3
                state['show_data_panel'] = True
                state['data_expanded'] = True
            if event.key == pygame.K_4:
                state['data_mode'] = 4
                state['show_data_panel'] = True
                state['data_expanded'] = True
            # Toggle data panel visibility: press 0 to hide/show
            if event.key == pygame.K_0:
                state['show_data_panel'] = not state.get('show_data_panel', True)
                # collapse when hiding
                if not state['show_data_panel']:
                    state['data_expanded'] = False
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
