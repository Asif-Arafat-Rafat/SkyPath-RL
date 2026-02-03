import random 
import math
def configT(W,H):
    hills = random.randint(7, 10)
    CENTERS = [(0,0),(800,600)]
    BASE_RADIUS = [100,100]
    attempts = 0
    max_attempts = 1000  
    transmitter_tower_height=random.randint(20,70)
    receiver_tower_height=random.randint(20,70)
    while len(CENTERS) < hills+5 and attempts < max_attempts:
        attempts += 1
        r = random.randint(30, 150)
        x = random.randint(r, W - r)
        y = random.randint(r, H - r)
        
        # check overlap
        overlap = False
        for (cx, cy, cr) in zip([c[0] for c in CENTERS], [c[1] for c in CENTERS], BASE_RADIUS):
            dist = math.hypot(cx - x, cy - y)
            if dist < r + cr + 10:  # +10 is margin
                overlap = True
                break
        
        if not overlap:
            CENTERS.append((x, y))
            BASE_RADIUS.append(r)

    print("Generated centers:", CENTERS)
    LAYERS = [random.randint(int(BASE_RADIUS[h]/10),int(BASE_RADIUS[h]/5)) for h in range(hills)]           # number of stacked circles
    LAYER_GAP = [BASE_RADIUS[h]/LAYERS[h]-1 for h in range(hills)]       # distance between layers
    NOISE_FREQ = [random.uniform(0.04,0.07) for _ in range(hills)]
    NOISE_AMP = [random.randint(4,5) for _ in range(hills)]
    return hills,LAYERS,CENTERS,BASE_RADIUS,LAYER_GAP,NOISE_FREQ,NOISE_AMP,transmitter_tower_height,receiver_tower_height
