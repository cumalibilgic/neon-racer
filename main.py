import asyncio
import math
import random
import sys

import pygame

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

_glow_cache = {}


def mix(c1, c2, t):
    t = max(0.0, min(1.0, t))
    return tuple(int(a + (b - a) * t) for a, b in zip(c1, c2))


def fog_amount(z):
    return max(0.0, min(0.85, (z - 14) / 46))


_glow_base = None


def glow_base():
    global _glow_base
    if _glow_base is None:
        size = 64
        _glow_base = pygame.Surface((size, size))
        half = size / 2
        for y in range(size):
            for x in range(size):
                d = math.hypot(x + 0.5 - half, y + 0.5 - half) / half
                v = int(255 * max(0.0, 1 - d) ** 2.2)
                _glow_base.set_at((x, y), (v, v, v))
    return _glow_base


def glow_sprite(color, rx, ry, level):
    key = (color, rx, ry, level)
    sprite = _glow_cache.get(key)
    if sprite is None:
        if len(_glow_cache) > 3000:
            _glow_cache.clear()
        sprite = pygame.transform.smoothscale(glow_base(), (rx * 4, ry * 4))
        sprite.fill(mix((0, 0, 0), color, level / 4), special_flags=pygame.BLEND_MULT)
        _glow_cache[key] = sprite
    return sprite


def blit_glow(surface, color, pos, radius, level=4, squash=1.0):
    rx = max(1, int(radius))
    ry = max(1, int(radius * squash))
    sprite = glow_sprite(color, rx, ry, max(1, min(4, int(level))))
    surface.blit(sprite, (int(pos[0]) - rx * 2, int(pos[1]) - ry * 2), special_flags=pygame.BLEND_ADD)


def draw_neon_text(surface, text, font, color, **position):
    base = font.render(text, True, color)
    shadow = font.render(text, True, (0, 0, 0))
    glow = font.render(text, True, mix((0, 0, 0), color, 0.45), (0, 0, 0))
    rect = base.get_rect(**position)
    for dx, dy in ((2, 3), (-1, 2), (3, 1), (0, 4)):
        surface.blit(shadow, rect.move(dx, dy))
    for dx, dy in ((-2, 0), (2, 0), (0, -2), (0, 2), (-1, -1), (1, 1), (-1, 1), (1, -1)):
        surface.blit(glow, rect.move(dx, dy), special_flags=pygame.BLEND_ADD)
    surface.blit(base, rect)


def make_sky():
    w, h = WIDTH * SS, (HORIZON + 2) * SS
    surf = pygame.Surface((w, h))
    for y in range(h):
        pygame.draw.line(surf, mix(SKY_TOP, SKY_BOTTOM, (y / (HORIZON * SS)) ** 1.6), (0, y), (w, y))
    rnd = random.Random(7)
    for _ in range(90):
        b = rnd.randint(90, 220)
        size = SS if rnd.random() < 0.8 else SS * 2
        pygame.draw.rect(surf, (b, b, min(255, b + 30)), (rnd.randrange(w), rnd.randrange(int(h * 0.7)), size, size))
    return surf


def make_sun(radius):
    size = radius * 2
    surf = pygame.Surface((size, size), pygame.SRCALPHA)
    for row in range(size):
        t = row / size
        if t > 0.5 and (row - radius) % (10 * SS) < (t - 0.5) * 14 * SS:
            continue
        dy = row - radius + 0.5
        half = math.sqrt(max(0.0, radius * radius - dy * dy))
        pygame.draw.line(surf, mix(YELLOW, MAGENTA, t), (radius - half, row), (radius + half, row))
    return surf


def make_skyline(width, height, color, window_color, density, seed):
    rnd = random.Random(seed)
    surf = pygame.Surface((width, height), pygame.SRCALPHA)
    x = 0
    while x < width:
        w = rnd.randint(24, 60) * SS
        h = rnd.randint(height // 3, height)
        pygame.draw.rect(surf, color, (x, height - h, w, h))
        pygame.draw.line(surf, mix(color, window_color, 0.35), (x, height - h), (x + w - 1, height - h), SS)
        for wy in range(height - h + 6 * SS, height - 4 * SS, 9 * SS):
            for wx in range(x + 4 * SS, x + w - 5 * SS, 7 * SS):
                if rnd.random() < density:
                    pygame.draw.rect(surf, window_color, (wx, wy, 3 * SS, 4 * SS))
        if rnd.random() < 0.3:
            pygame.draw.line(surf, color, (x + w // 2, height - h), (x + w // 2, height - h - 12 * SS), 2 * SS)
            pygame.draw.rect(surf, RED, (x + w // 2 - SS, height - h - 13 * SS, 2 * SS, 2 * SS))
        x += w + rnd.randint(0, 6) * SS
    return surf


def make_haze(height, max_alpha, upward=False):
    surf = pygame.Surface((WIDTH * SS, height), pygame.SRCALPHA)
    for y in range(height):
        t = y / height
        if upward:
            t = 1 - t
        pygame.draw.line(surf, (*FOG, int(max_alpha * (1 - t) ** 1.8)), (0, y), (WIDTH * SS, y))
    return surf


def make_vignette():
    small = pygame.Surface((48, 72), pygame.SRCALPHA)
    for y in range(72):
        for x in range(48):
            dx = (x + 0.5) / 48 * 2 - 1
            dy = (y + 0.5) / 72 * 2 - 1
            d = math.sqrt(dx * dx * 0.9 + dy * dy * 0.75)
            small.set_at((x, y), (0, 0, 0, int(max(0.0, min(1.0, (d - 0.6) / 0.6)) * 160)))
    return pygame.transform.smoothscale(small, (WIDTH, HEIGHT))


def draw_car(surface, x, y, s, color, tilt=0.0, player=False, boost=False, fog=0.0):
    w, h = CAR_W * s, CAR_H * s
    if w < 3:
        return

    def f(col):
        return mix(col, FOG, fog) if fog else col

    glow_level = max(1, round(3 * (1 - fog)))
    red = f(RED)
    dark = f(mix(color, (0, 0, 0), 0.45))
    light = f(mix(color, WHITE, 0.35))
    shine = f(mix(color, WHITE, 0.12))
    color = f(color)

    pygame.draw.ellipse(surface, (4, 3, 10), (x - w * 0.6, y - h * 0.14, w * 1.2, h * 0.28))
    if player:
        blit_glow(surface, CYAN if boost else (40, 110, 255), (x, y - h * 0.02), w * 0.5, 4 if boost else 3, 0.28)

    wheel_w, wheel_h = w * 0.17, h * 0.3
    for wx in (x - w * 0.5, x + w * 0.5 - wheel_w):
        pygame.draw.rect(surface, f((12, 12, 18)), (wx, y - wheel_h, wheel_w, wheel_h), border_radius=max(1, int(3 * s)))

    shift = tilt * w * 0.08
    cabin = [(x - w * 0.4, y - h * 0.6), (x + w * 0.4, y - h * 0.6),
             (x + w * 0.3 + shift, y - h), (x - w * 0.3 + shift, y - h)]
    pygame.draw.polygon(surface, dark, cabin)
    glass = [(x - w * 0.33, y - h * 0.63), (x + w * 0.33, y - h * 0.63),
             (x + w * 0.25 + shift, y - h * 0.93), (x - w * 0.25 + shift, y - h * 0.93)]
    pygame.draw.polygon(surface, f(DARK_GLASS), glass)
    pygame.draw.line(surface, f(mix(DARK_GLASS, WHITE, 0.3)), glass[3], glass[2], max(1, int(s)))
    pygame.draw.line(surface, f(mix(DARK_GLASS, WHITE, 0.15)),
                     (glass[0][0] + w * 0.12, glass[0][1]), (glass[3][0] + w * 0.2, glass[3][1]), max(1, int(2 * s)))

    body = pygame.Rect(0, 0, w, h * 0.46)
    body.midbottom = (x, y - h * 0.12)
    pygame.draw.rect(surface, color, body, border_radius=max(1, int(7 * s)))
    upper = pygame.Rect(body.x, body.y, body.w, body.h * 0.45)
    pygame.draw.rect(surface, shine, upper, border_top_left_radius=max(1, int(7 * s)), border_top_right_radius=max(1, int(7 * s)))
    pygame.draw.line(surface, light, (body.left + w * 0.06, body.top + 1), (body.right - w * 0.06, body.top + 1), max(1, int(2 * s)))
    pygame.draw.line(surface, dark, (body.left + w * 0.08, body.bottom - h * 0.08), (body.right - w * 0.08, body.bottom - h * 0.08), max(1, int(3 * s)))

    light_w, light_h = w * 0.27, max(2, h * 0.09)
    ly = body.top + h * 0.1
    for lx in (body.left + w * 0.05, body.right - w * 0.05 - light_w):
        pygame.draw.rect(surface, red, (lx, ly, light_w, light_h), border_radius=max(1, int(2 * s)))
        blit_glow(surface, red, (lx + light_w / 2, ly + light_h / 2), 1.5 * SS + w * 0.1, glow_level)
        if fog < 0.5:
            for k in (1, 2, 3):
                blit_glow(surface, red, (lx + light_w / 2, y + h * 0.04 + k * h * 0.11), (SS + w * 0.05) * (1 - k * 0.2), 1)

    plate = pygame.Rect(0, 0, w * 0.22, h * 0.09)
    plate.center = (x, body.centery + h * 0.06)
    pygame.draw.rect(surface, f((200, 200, 220)), plate, border_radius=1)

    if player:
        spoiler_y = body.top - h * 0.06
        pygame.draw.line(surface, dark, (x - w * 0.46, spoiler_y), (x + w * 0.46, spoiler_y), max(2, int(4 * s)))
        pygame.draw.line(surface, CYAN, (body.left + w * 0.12, body.centery), (body.right - w * 0.12, body.centery), 1)


def draw_lamp(surface, x, y, s, side, fog=0.0):
    h = 160 * s
    top = (x, y - h)
    head = (x - side * 26 * s, y - h)
    pole = mix((85, 75, 125), FOG, fog)
    color = CYAN if side < 0 else MAGENTA
    level = max(1, round(4 * (1 - fog)))
    pygame.draw.line(surface, pole, (x, y), top, max(1, int(5 * s)))
    pygame.draw.line(surface, pole, top, head, max(1, int(4 * s)))
    blit_glow(surface, color, head, 2 * SS + 14 * s, level)
    if fog < 0.6:
        for k in (1, 2):
            blit_glow(surface, color, (head[0], y + k * 9 * s), (SS + 8 * s) / k, 1)


class Particle:
    def __init__(self, x, y, vx, vy, life, color, size, gravity=0.0, drag=0.97):
        self.x, self.y = x, y
        self.vx, self.vy = vx, vy
        self.life = self.max_life = life
        self.color = color
        self.size = size
        self.gravity = gravity
        self.drag = drag

    def update(self):
        self.vx *= self.drag
        self.vy = self.vy * self.drag + self.gravity
        self.x += self.vx
        self.y += self.vy
        self.life -= 1
        return self.life > 0

    def draw(self, surface):
        t = self.life / self.max_life
        blit_glow(surface, self.color, (self.x, self.y), self.size * (0.4 + 0.6 * t), round(1 + 3 * t))


class Car:
    def __init__(self, lane, z, color):
        self.lane = lane
        self.z = z
        self.color = color


class Pad:
    def __init__(self, lane, z):
        self.lane = lane
        self.z = z


class Game:
    def __init__(self):
        self.font = pygame.font.Font(None, 30)
        self.small_font = pygame.font.Font(None, 24)
        self.big_font = pygame.font.Font(None, 76)
        self.canvas = pygame.Surface((WIDTH * SS, HEIGHT * SS))
        self.sky = make_sky()
        self.sun = make_sun(88 * SS)
        self.skyline_far = make_skyline(WIDTH * 2 * SS, 72 * SS, (34, 12, 58), (130, 70, 170), 0.16, 1)
        self.skyline_near = make_skyline(WIDTH * 2 * SS, 96 * SS, (14, 8, 28), (255, 200, 90), 0.1, 2)
        self.haze = make_haze(110 * SS, 215)
        self.sky_haze = make_haze(70 * SS, 120, upward=True)
        self.vignette = make_vignette()
        self.road_zs = [Z_FAR * (i / ROAD_SEGMENTS) ** 2 for i in range(ROAD_SEGMENTS + 1)]
        self.high_score = 0
        self.time = 0
        self.state = "menu"
        self.reset()

    def reset(self):
        self.lane = 1
        self.player_x = float(LANES[1])
        self.score = 0.0
        self.speed = START_SPEED
        self.boost = False
        self.boost_timer = 0
        self.traffic = []
        self.pads = []
        self.particles = []
        self.speed_lines = []
        self.spawn_timer = 60
        self.distance = 0.0
        self.curve = 0.0
        self.curve_target = 0.0
        self.curve_timer = 240
        self.sky_offset = 0.0
        self.shake = 0.0
        self.flash = 0
        self.over_timer = 0

    def start(self):
        self.reset()
        self.state = "play"

    def project(self, xw, z):
        s = CAM / (CAM + z)
        y = HORIZON + (BASE_Y - HORIZON) * s
        x = WIDTH / 2 + self.curve * (1 - s) ** 2 * 220 + xw * s
        return x * SS, y * SS, s * SS

    def handle_event(self, event):
        can_start = self.state == "menu" or (self.state == "over" and self.over_timer > 30)
        if event.type == pygame.KEYDOWN:
            if self.state == "play":
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    self.lane = max(0, self.lane - 1)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.lane = min(2, self.lane + 1)
            elif can_start and event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_r):
                self.start()
        elif event.type == pygame.MOUSEBUTTONDOWN:
            if self.state == "play":
                if event.pos[0] < WIDTH // 2:
                    self.lane = max(0, self.lane - 1)
                else:
                    self.lane = min(2, self.lane + 1)
            elif can_start:
                self.start()

    def update(self):
        self.time += 1

        if self.state == "play":
            base = min(START_SPEED + self.score / 1500, MAX_SPEED)
            if self.boost:
                self.boost_timer -= 1
                if self.boost_timer <= 0:
                    self.boost = False
            target_speed = base * 1.5 if self.boost else base
            self.speed += (target_speed - self.speed) * 0.08
        elif self.state == "menu":
            self.speed += (4 - self.speed) * 0.05
        else:
            self.speed *= 0.95
            self.over_timer += 1

        step = self.speed * Z_PER_SPEED
        self.distance += step

        self.curve_timer -= 1
        if self.curve_timer <= 0:
            self.curve_target = random.uniform(-1, 1)
            self.curve_timer = random.randint(180, 420)
        self.curve += (self.curve_target - self.curve) * 0.01
        self.sky_offset += self.curve * self.speed * 0.25

        self.player_x += (LANES[self.lane] - self.player_x) * 0.22

        if self.state == "play":
            self.spawn_timer -= 1
            if self.spawn_timer <= 0:
                self.spawn()
                self.spawn_timer = int(max(14, random.randint(30, 60) * START_SPEED / self.speed))

        for car in self.traffic:
            car.z -= step
        for pad in self.pads:
            pad.z -= step
        self.traffic = [car for car in self.traffic if car.z > -1.5]
        self.pads = [pad for pad in self.pads if pad.z > -1.5]

        if self.state == "play":
            self.score += self.speed * 0.1
            self.emit_exhaust()
            self.check_collisions()
        elif self.state == "menu":
            self.emit_exhaust()
        elif self.time % 3 == 0:
            x, y, s = self.project(self.player_x, PLAYER_Z)
            self.particles.append(Particle(x + random.uniform(-15, 15) * SS, y - CAR_H * s * 0.8,
                                           random.uniform(-0.4, 0.4) * SS, random.uniform(-2, -1) * SS,
                                           random.randint(35, 55), (70, 60, 90), random.uniform(4, 7) * SS, 0, 0.99))

        self.update_effects()

    def spawn(self):
        busy = {car.lane for car in self.traffic if car.z > Z_FAR - 9}
        lane = random.randrange(3)
        if lane in busy or len(busy) >= 2:
            return
        self.traffic.append(Car(lane, Z_FAR, random.choice(TRAFFIC_COLORS)))
        if random.random() < 0.18:
            self.pads.append(Pad(random.choice([i for i in range(3) if i != lane]), Z_FAR + 3))

    def emit_exhaust(self):
        x, y, s = self.project(self.player_x, PLAYER_Z)
        w, h = CAR_W * s, CAR_H * s
        for side in (-1, 1):
            px, py = x + side * w * 0.28, y - h * 0.2
            if self.boost:
                for _ in range(2):
                    self.particles.append(Particle(px + random.uniform(-2, 2) * SS, py, random.uniform(-0.6, 0.6) * SS,
                                                   random.uniform(3, 6) * SS, random.randint(14, 24),
                                                   random.choice([CYAN, YELLOW, WHITE]), random.uniform(3, 5) * SS))
            elif self.time % 2 == 0:
                self.particles.append(Particle(px, py, random.uniform(-0.3, 0.3) * SS, random.uniform(1.5, 3) * SS,
                                               random.randint(16, 26), (110, 90, 170), random.uniform(2, 3.5) * SS))

    def burst(self, x, y, count, colors, speed_range, life_range, size_range, gravity):
        for _ in range(count):
            angle = random.uniform(0, math.tau)
            v = random.uniform(*speed_range) * SS
            self.particles.append(Particle(x, y, math.cos(angle) * v, math.sin(angle) * v - 1.5 * SS,
                                           random.randint(*life_range), random.choice(colors),
                                           random.uniform(*size_range) * SS, gravity * SS, 0.96))

    def check_collisions(self):
        for pad in self.pads[:]:
            if abs(pad.z - PLAYER_Z) < 0.9 and abs(LANES[pad.lane] - self.player_x) < 70:
                self.pads.remove(pad)
                self.boost = True
                self.boost_timer = BOOST_TIME
                x, y, s = self.project(self.player_x, PLAYER_Z)
                self.burst(x, y - 20 * SS, 40, [CYAN, WHITE, YELLOW], (2, 7), (30, 55), (2, 4), 0.1)

        for car in self.traffic:
            if abs(car.z - PLAYER_Z) < CAR_DEPTH and abs(LANES[car.lane] - self.player_x) < CAR_W * 0.8:
                self.crash(car)
                break

    def crash(self, car):
        self.state = "over"
        self.over_timer = 0
        self.boost = False
        self.high_score = max(self.high_score, int(self.score))
        self.traffic.remove(car)
        x, y, s = self.project(self.player_x, PLAYER_Z)
        self.burst(x, y - 30 * SS, 90, [ORANGE, YELLOW, MAGENTA, RED, WHITE], (2, 11), (40, 90), (2, 5), 0.12)
        self.shake = 18.0
        self.flash = 140

    def update_effects(self):
        self.particles = [p for p in self.particles if p.update()]
        if len(self.particles) > 700:
            self.particles = self.particles[-700:]

        if self.state == "play" and (self.boost or (self.speed > 11 and self.time % 3 == 0)):
            for _ in range(3 if self.boost else 1):
                self.speed_lines.append([random.uniform(0, math.tau), random.uniform(20, 80) * SS, random.uniform(4, 8) * SS])
        for line in self.speed_lines:
            line[1] += line[2]
            line[2] *= 1.08
        self.speed_lines = [line for line in self.speed_lines if line[1] < 800 * SS]

        self.shake *= 0.88
        if self.shake < 0.3:
            self.shake = 0.0
        self.flash = max(0, self.flash - 12)

    def quad(self, surface, color, xf, yf, sf, xn, yn, sn, x0, x1):
        pygame.draw.polygon(surface, color, [(xf + x0 * sf, yf), (xf + x1 * sf, yf),
                                             (xn + x1 * sn, yn), (xn + x0 * sn, yn)])

    def draw_background(self, c):
        c.blit(self.sky, (0, 0))
        vx, _, _ = self.project(0, 400)
        sun_rect = self.sun.get_rect(midbottom=(int(vx), (HORIZON + 30) * SS))
        blit_glow(c, MAGENTA, sun_rect.center, 70 * SS, 2)
        c.blit(self.sun, sun_rect)

        for layer, factor in ((self.skyline_far, 0.35), (self.skyline_near, 0.7)):
            lw = layer.get_width()
            offset = int((-self.sky_offset * factor - self.curve * 60 * factor) * SS) % lw
            y = (HORIZON + 2) * SS - layer.get_height()
            c.blit(layer, (offset - lw, y))
            c.blit(layer, (offset, y))

        c.blit(self.sky_haze, (0, HORIZON * SS - self.sky_haze.get_height()))
        pygame.draw.rect(c, GROUND, (0, HORIZON * SS, WIDTH * SS, (HEIGHT - HORIZON) * SS))
        zs = self.road_zs[::8]
        for xw in range(-2200, 2201, 220):
            if abs(xw) < ROAD_HALF + 60:
                continue
            pygame.draw.lines(c, GRID_DIM, False, [self.project(xw, z)[:2] for z in zs], SS)
        pygame.draw.line(c, MAGENTA, (0, HORIZON * SS), (WIDTH * SS, HORIZON * SS), 2 * SS)

    def draw_road(self, c):
        zs = self.road_zs
        d = self.distance
        for i in range(len(zs) - 1, 0, -1):
            zf, zn = zs[i], zs[i - 1]
            xf, yf, sf = self.project(0, zf)
            xn, yn, sn = self.project(0, zn)

            rn = sn / SS
            fog = fog_amount(zn)

            if int((zn + d) / 4) != int((zf + d) / 4):
                pygame.draw.line(c, mix(GROUND, GRID, 0.3 + rn), (0, yn), (WIDTH * SS, yn), SS if rn < 0.4 else 2 * SS)

            road_color = ROAD_A if int((zn + d) / 3) % 2 == 0 else ROAD_B
            self.quad(c, mix(road_color, FOG, fog), xf, yf, sf, xn, yn, sn, -ROAD_HALF, ROAD_HALF)

            for side, color in ((-1, CYAN), (1, MAGENTA)):
                ex = side * ROAD_HALF
                for half_w, k in ((18, 0.25), (8, 0.55), (3, 1.0)):
                    self.quad(c, mix(ROAD_A, color, k), xf, yf, sf, xn, yn, sn, ex - half_w, ex + half_w)

            if (zn + d) % 4 < 2:
                lane_color = mix(mix(ROAD_A, WHITE, 0.35 + 0.65 * rn), FOG, fog)
                for lx in (-LANE_W / 2, LANE_W / 2):
                    self.quad(c, lane_color, xf, yf, sf, xn, yn, sn, lx - 3, lx + 3)

    def draw_pad(self, c, pad):
        z0, z1 = pad.z - 0.6, pad.z + 0.6
        if z0 < -1 or z1 > Z_FAR:
            return
        xn, yn, sn = self.project(0, z0)
        xf, yf, sf = self.project(0, z1)
        lx = LANES[pad.lane]
        pulse = 0.6 + 0.4 * math.sin(self.time * 0.2)
        self.quad(c, mix(ROAD_A, CYAN, 0.2 + 0.35 * pulse), xf, yf, sf, xn, yn, sn, lx - 55, lx + 55)
        for t in (0.15, 0.55):
            bx, by, bs = self.project(lx, z0 + (z1 - z0) * t)
            tx, ty, _ = self.project(lx, z0 + (z1 - z0) * (t + 0.3))
            pygame.draw.lines(c, CYAN, False, [(bx - 35 * bs, by), (tx, ty), (bx + 35 * bs, by)], max(1, int(5 * bs)))
        cx, cy, cs = self.project(lx, pad.z)
        blit_glow(c, CYAN, (cx, cy), max(2, 30 * cs), 2)

    def draw_objects(self, c):
        for pad in self.pads:
            self.draw_pad(c, pad)

        items = [(car.z, 0, car) for car in self.traffic if car.z < Z_FAR]
        z = LAMP_GAP - (self.distance % LAMP_GAP) - LAMP_GAP
        while z < Z_FAR:
            if z > -1.5:
                items.append((z, 1, -1))
                items.append((z, 1, 1))
            z += LAMP_GAP
        items.append((PLAYER_Z, 2, None))
        items.sort(key=lambda item: -item[0])

        for z, kind, obj in items:
            if kind == 0:
                x, y, s = self.project(LANES[obj.lane], z)
                draw_car(c, x, y, s, obj.color, fog=fog_amount(z))
            elif kind == 1:
                x, y, s = self.project(obj * LAMP_X, z)
                draw_lamp(c, x, y, s, obj, fog_amount(z))
            else:
                x, y, s = self.project(self.player_x, PLAYER_Z)
                tilt = (LANES[self.lane] - self.player_x) / LANE_W
                color = (60, 60, 80) if self.state == "over" else PLAYER_COLOR
                draw_car(c, x, y, s, color, tilt, True, self.boost)

    def draw_speed_lines(self, c):
        vx, vy, _ = self.project(0, 400)
        for angle, r, _ in self.speed_lines:
            ca, sa = math.cos(angle), math.sin(angle)
            r2 = r + 15 * SS + r * 0.3
            color = mix(BG, WHITE, min(1.0, r / (400 * SS)) * 0.8)
            pygame.draw.line(c, color, (vx + ca * r, vy + sa * r), (vx + ca * r2, vy + sa * r2), SS if r < 250 * SS else 2 * SS)

    def draw_hud(self, screen):
        if self.state in ("play", "over"):
            draw_neon_text(screen, "NEON RACER", self.small_font, MAGENTA, topleft=(14, 14))
            draw_neon_text(screen, f"SCORE {int(self.score)}", self.font, WHITE, topright=(WIDTH - 14, 12))
            draw_neon_text(screen, f"{int(self.speed * 18)} KM/H", self.small_font, CYAN, topright=(WIDTH - 14, 40))
            if self.boost:
                draw_neon_text(screen, "BOOST!", self.font, YELLOW, topleft=(14, 38))
                pygame.draw.rect(screen, (60, 50, 20), (14, 66, 110, 6), border_radius=3)
                pygame.draw.rect(screen, YELLOW, (14, 66, int(110 * self.boost_timer / BOOST_TIME), 6), border_radius=3)

        if self.state == "menu":
            self.draw_menu(screen)
        elif self.state == "over" and self.over_timer > 25:
            self.draw_game_over(screen)

    def draw_panel(self, screen, rect, color):
        panel = pygame.Surface(rect.size, pygame.SRCALPHA)
        panel.fill((5, 5, 15, 175))
        screen.blit(panel, rect)
        pygame.draw.rect(screen, color, rect, 1, border_radius=8)

    def draw_menu(self, screen):
        t = (math.sin(self.time * 0.05) + 1) / 2
        draw_neon_text(screen, "NEON RACER", self.big_font, mix(CYAN, MAGENTA, t), center=(WIDTH // 2, 90))
        draw_neon_text(screen, "DODGE  /  BOOST  /  SURVIVE", self.small_font, WHITE, center=(WIDTH // 2, 140))

        self.draw_panel(screen, pygame.Rect(40, 380, WIDTH - 80, 140), CYAN)
        lines = ["Yön tuşları / A - D : şerit değiştir",
                 "Dokunmatik: ekranın sol / sağ yarısı",
                 "Mavi pad'ler: 3 saniye BOOST"]
        for i, text in enumerate(lines):
            draw_neon_text(screen, text, self.small_font, WHITE, center=(WIDTH // 2, 410 + i * 34))
        if self.high_score:
            draw_neon_text(screen, f"En iyi: {self.high_score}", self.font, YELLOW, center=(WIDTH // 2, 545))
        if (self.time // 30) % 2 == 0:
            draw_neon_text(screen, "SPACE veya TIKLA: BAŞLA", self.font, CYAN, center=(WIDTH // 2, 590))

    def draw_game_over(self, screen):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        screen.blit(overlay, (0, 0))
        draw_neon_text(screen, "GAME OVER", self.big_font, MAGENTA, center=(WIDTH // 2, 280))
        draw_neon_text(screen, f"Skor: {int(self.score)}", self.font, WHITE, center=(WIDTH // 2, 345))
        draw_neon_text(screen, f"En iyi: {self.high_score}", self.font, YELLOW, center=(WIDTH // 2, 380))
        if (self.time // 30) % 2 == 0:
            draw_neon_text(screen, "SPACE veya TIKLA: tekrar oyna", self.font, CYAN, center=(WIDTH // 2, 440))

    def draw(self, screen):
        c = self.canvas
        self.draw_background(c)
        self.draw_road(c)
        c.blit(self.haze, (0, HORIZON * SS))
        self.draw_objects(c)
        for particle in self.particles:
            particle.draw(c)
        self.draw_speed_lines(c)

        frame = c if SS == 1 else pygame.transform.smoothscale(c, (WIDTH, HEIGHT))

        ox = oy = 0
        if self.shake:
            ox = int(random.uniform(-self.shake, self.shake))
            oy = int(random.uniform(-self.shake, self.shake))
        screen.fill(BG)
        screen.blit(frame, (ox, oy))

        if BLOOM:
            small = pygame.transform.smoothscale(frame, (WIDTH // 4, HEIGHT // 4))
            small.blit(small.copy(), (0, 0), special_flags=pygame.BLEND_MULT)
            small.fill((170, 170, 170), special_flags=pygame.BLEND_MULT)
            screen.blit(pygame.transform.smoothscale(small, (WIDTH, HEIGHT)), (ox, oy), special_flags=pygame.BLEND_ADD)

        screen.blit(self.vignette, (0, 0))

        if self.flash:
            flash = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            flash.fill((255, 240, 220, self.flash))
            screen.blit(flash, (0, 0))

        self.draw_hud(screen)


async def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Neon Racer")
    clock = pygame.time.Clock()
    game = Game()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                return
            game.handle_event(event)

        game.update()
        game.draw(screen)
        pygame.display.flip()
        await asyncio.sleep(0)
        clock.tick(FPS)


asyncio.run(main())