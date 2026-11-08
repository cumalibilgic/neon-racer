"""Small mutable entities used by the game simulation."""

from config import SS
from rendering import blit_glow

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


class Coin:
    def __init__(self, lane, z):
        self.lane = lane
        self.z = z


class ShieldPickup:
    def __init__(self, lane, z):
        self.lane = lane
        self.z = z
