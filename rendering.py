"""Reusable drawing primitives for the synthwave scene."""

import math
import random

import pygame

from config import *  # noqa: F403

_glow_cache = {}

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


def draw_coin(surface, x, y, scale, phase=0.0):
    radius = max(3, int(13 * scale))
    width = max(2, int(radius * (0.3 + 0.7 * abs(math.cos(phase)))))
    blit_glow(surface, YELLOW, (x, y), radius * 1.7, 2, 0.8)
    pygame.draw.ellipse(surface, (117, 67, 12), (x - width - 2, y - radius - 2, (width + 2) * 2, (radius + 2) * 2))
    pygame.draw.ellipse(surface, YELLOW, (x - width, y - radius, width * 2, radius * 2))
    pygame.draw.line(surface, (255, 248, 177), (x, y - radius * 0.55), (x, y + radius * 0.55), max(1, int(scale * 2)))


def draw_shield(surface, x, y, scale=1.0, phase=0.0):
    radius = max(6, int(15 * scale))
    pulse = 1.0 + 0.08 * math.sin(phase)
    half_width = radius * pulse
    points = [
        (x, y - radius * 1.15),
        (x + half_width, y - radius * 0.82),
        (x + half_width * 0.82, y + radius * 0.18),
        (x, y + radius * 1.15),
        (x - half_width * 0.82, y + radius * 0.18),
        (x - half_width, y - radius * 0.82),
    ]
    blit_glow(surface, CYAN, (x, y), radius * 1.8, 2, 1.1)
    pygame.draw.polygon(surface, (8, 38, 58), points)
    pygame.draw.polygon(surface, CYAN, points, max(1, int(2 * scale)))
    pygame.draw.line(surface, (205, 255, 255), (x - radius * 0.38, y), (x - radius * 0.06, y + radius * 0.34), max(1, int(2 * scale)))
    pygame.draw.line(surface, (205, 255, 255), (x - radius * 0.06, y + radius * 0.34), (x + radius * 0.42, y - radius * 0.3), max(1, int(2 * scale)))
