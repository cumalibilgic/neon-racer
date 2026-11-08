"""Shared game dimensions, tuning values, palette, and small math helpers."""

import sys

WIDTH, HEIGHT = 480, 720
FPS = 60

WEB = sys.platform == "emscripten"
SS = 1 if WEB else 2
BLOOM = True

HORIZON = 250
BASE_Y = HEIGHT + 80
CAM = 4.0
Z_FAR = 60.0
PLAYER_Z = 1.3
ROAD_SEGMENTS = 72

LANE_W = 150
ROAD_HALF = 225
LAMP_X = 290
LAMP_GAP = 7
LANES = [-LANE_W, 0, LANE_W]

CAR_W, CAR_H = 100, 66
CAR_DEPTH = 1.1

START_SPEED = 6
MAX_SPEED = 13
BOOST_TIME = 180
Z_PER_SPEED = 0.03

SWIPE_DIST = 40

BG = (8, 6, 20)
SKY_TOP = (6, 4, 20)
SKY_BOTTOM = (70, 12, 80)
GROUND = (10, 6, 24)
GRID = (120, 30, 150)
GRID_DIM = (45, 14, 70)
ROAD_A = (24, 24, 40)
ROAD_B = (30, 30, 50)
CYAN = (0, 230, 255)
MAGENTA = (255, 0, 200)
WHITE = (235, 240, 255)
YELLOW = (255, 210, 60)
ORANGE = (255, 140, 40)
RED = (255, 40, 60)
DARK_GLASS = (15, 18, 30)
FOG = (66, 14, 78)
PLAYER_COLOR = (30, 120, 255)
TRAFFIC_COLORS = [(255, 60, 80), (255, 150, 0), (170, 70, 255), (40, 220, 140), (240, 240, 250)]

def mix(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def fog_amount(z):
    return max(0.0, min(0.85, (z - 14) / 46))

__all__ = ['WIDTH', 'HEIGHT', 'FPS', 'WEB', 'SS', 'BLOOM', 'HORIZON', 'BASE_Y', 'CAM', 'Z_FAR', 'PLAYER_Z', 'ROAD_SEGMENTS', 'LANE_W', 'ROAD_HALF', 'LAMP_X', 'LAMP_GAP', 'LANES', 'CAR_W', 'CAR_H', 'CAR_DEPTH', 'START_SPEED', 'MAX_SPEED', 'BOOST_TIME', 'Z_PER_SPEED', 'SWIPE_DIST', 'BG', 'SKY_TOP', 'SKY_BOTTOM', 'GROUND', 'GRID', 'GRID_DIM', 'ROAD_A', 'ROAD_B', 'CYAN', 'MAGENTA', 'WHITE', 'YELLOW', 'ORANGE', 'RED', 'DARK_GLASS', 'FOG', 'PLAYER_COLOR', 'TRAFFIC_COLORS', 'mix', 'fog_amount']
