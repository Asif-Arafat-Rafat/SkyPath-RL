def drone_config(n=0):
    drones=[]
    for i in range(n):
        drone_x,drone_y,drone_z=50+30*i,50,10
        drones.append([drone_x,drone_y,drone_z])
    speed=2
    range_=200
    return drones,speed,range_