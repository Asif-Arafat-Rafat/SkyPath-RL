from elements.terrain import draw_terrain
from elements.distance import calculate_distance
import configFiles.configM as cf
once = False

def terrain_moderator(screen,font,overlay,tower_connection=False):
    global once
    inter_points,visited,heights=draw_terrain(screen,font,overlay,tower_connection)
    lst=[sub for sub in inter_points if sub]
    result = [sub if len(sub) <= 2 else [sub[0], sub[-1]] for sub in lst]
    distances = []
    for sublist in result:
        if len(sublist) == 2:
            dist = calculate_distance(sublist[0], sublist[1])
            distances.append(dist*cf.scale)
    if not once:
        print(f"inter_points: {inter_points}")
        print(f"heights: {[heights[f] for f in visited]}")
        once = True
    return result, distances