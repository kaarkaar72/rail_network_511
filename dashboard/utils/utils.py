CATEGORY_COLOR_MAP = {
    "Express Passenger": [255, 0, 0],       # Red
    "Ordinary Passenger": [255, 140, 0],    # Orange
    "Unadvertised Ordinary Passenger": [255, 215, 0], # Yellow
    "Staff Train": [255, 215, 0],
    "London Underground/Metro Service": [255, 215, 0],

    "ECS": [128, 0, 128],   # Purple
    "Empty Coaching Stock": [128, 0, 128],

    "Freight": [0, 100, 255],   # Blue
    "Postal": [0, 100, 255],
    "Departmental": [0, 100, 255],

    "Light Locomotive": [160, 160, 160],  # Gray

    "Bus": [0, 180, 0], # Green
    "Ship": [0, 180, 0]
}

ASSOC_COLOR = {
    "join": [0, 200, 0],      # green
    "divide": [255, 140, 0],  # orange
    "next": [155, 48, 255],   # purple
}

def hex_to_rgb(hex_color):
    if not hex_color or not isinstance(hex_color, str):
        return [150, 150, 150]
    s = hex_color.lstrip("#")
    try:
        return [int(s[i:i+2], 16) for i in (0, 2, 4)]
    except:
        return [150, 150, 150]

def category_to_color(cat):
    for key, val in CATEGORY_COLOR_MAP.items():
        if key.lower() in str(cat).lower():
            return val
    return [200, 200, 200]  # default gray