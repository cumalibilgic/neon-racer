"""Game state, input handling, simulation, and frame composition."""

import math
import random

import pygame

import storage
from audio import Audio
from config import *  # noqa: F403
from entities import Car, Pad, Particle
from rendering import (
    blit_glow, draw_car, draw_lamp, draw_neon_text, make_haze, make_sky,
    make_skyline, make_sun, make_vignette,
)

class Game:
    def __init__(self):
        self.font = pygame.font.Font(None, 30)
        self.small_font = pygame.font.Font(None, 24)
        self.mid_font = pygame.font.Font(None, 48)
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
        self.data = storage.load()
        self.high_score = int(self.data.get("high_score", 0))
        self.audio = Audio(muted=bool(self.data.get("muted", False)))
        if not WEB:
            self.audio.start_music()
        self.press = None
        self.swiped = False
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
        self.new_record = False

    def start(self):
        self.reset()
        self.state = "play"
        self.audio.play("start")
        self.audio.set_music_level(1.0)

    def save(self):
        self.data["high_score"] = self.high_score
        self.data["muted"] = self.audio.muted
        storage.save(self.data)

    def toggle_mute(self):
        self.audio.toggle_mute()
        self.save()

    def move(self, direction):
        lane = max(0, min(2, self.lane + direction))
        if lane != self.lane:
            self.lane = lane
            self.audio.play("lane")

    def mute_rect(self):
        if self.state == "menu":
            return pygame.Rect(WIDTH - 54, 12, 42, 42)
        if self.state == "over" and self.over_timer > 25:
            return pygame.Rect(WIDTH // 2 - 21, 490, 42, 42)
        return None

    def project(self, xw, z):
        s = CAM / (CAM + z)
        y = HORIZON + (BASE_Y - HORIZON) * s
        x = WIDTH / 2 + self.curve * (1 - s) ** 2 * 220 + xw * s
        return x * SS, y * SS, s * SS

    def can_start(self):
        return self.state == "menu" or (self.state == "over" and self.over_timer > 30)

    def handle_event(self, event):
        if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
            self.audio.start_music()

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_m:
                self.toggle_mute()
            elif self.state == "play":
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    self.move(-1)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self.move(1)
            elif self.can_start() and event.key in (pygame.K_SPACE, pygame.K_RETURN, pygame.K_r):
                self.start()
        # Telefonda dokunmalar da fare olayı olarak gelir.
        # Yatay kaydırma eşiği geçtiği anda şerit değişir; kaydırma olmadan bırakılan dokunuş "tıklama" sayılır.
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self.press = event.pos
            self.swiped = False
        elif event.type == pygame.MOUSEMOTION and self.press:
            dx = event.pos[0] - self.press[0]
            dy = event.pos[1] - self.press[1]
            if abs(dx) > SWIPE_DIST and abs(dx) > abs(dy):
                if self.state == "play":
                    self.move(1 if dx > 0 else -1)
                # Başlangıç noktasını kaydır ki uzun bir kaydırma iki şerit geçebilsin
                self.press = (event.pos[0], self.press[1])
                self.swiped = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.press:
            if not self.swiped:
                self.tap(self.press)
            self.press = None

    def tap(self, pos):
        mute = self.mute_rect()
        if mute and mute.inflate(16, 16).collidepoint(pos):
            self.toggle_mute()
        elif self.state == "play":
            self.move(-1 if pos[0] < WIDTH // 2 else 1)
        elif self.can_start():
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
                self.audio.play("boost")
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
        if int(self.score) > self.high_score:
            # İlk oyunda değil, var olan bir rekor geçildiğinde kutla
            self.new_record = self.high_score > 0
            self.high_score = int(self.score)
            self.save()
        self.audio.play("crash")
        self.audio.set_music_level(0.5)
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

    def draw_mute_button(self, screen):
        rect = self.mute_rect()
        if not rect:
            return
        color = MAGENTA if self.audio.muted else CYAN
        self.draw_panel(screen, rect, color)
        x, y = rect.centerx - 5, rect.centery
        pygame.draw.polygon(screen, color, [(x - 10, y - 5), (x - 4, y - 5), (x + 3, y - 11),
                                            (x + 3, y + 11), (x - 4, y + 5), (x - 10, y + 5)])
        if self.audio.muted:
            pygame.draw.line(screen, color, (x + 8, y - 6), (x + 18, y + 6), 3)
            pygame.draw.line(screen, color, (x + 8, y + 6), (x + 18, y - 6), 3)
        else:
            for radius in (7, 13):
                pygame.draw.arc(screen, color, (x + 3 - radius, y - radius, radius * 2, radius * 2), -0.8, 0.8, 2)

    def draw_menu(self, screen):
        t = (math.sin(self.time * 0.05) + 1) / 2
        draw_neon_text(screen, "NEON RACER", self.big_font, mix(CYAN, MAGENTA, t), center=(WIDTH // 2, 90))
        draw_neon_text(screen, "DODGE  /  BOOST  /  SURVIVE", self.small_font, WHITE, center=(WIDTH // 2, 140))
        self.draw_mute_button(screen)

        self.draw_panel(screen, pygame.Rect(40, 380, WIDTH - 80, 140), CYAN)
        lines = ["Yön tuşları / A - D : şerit değiştir",
                 "Telefonda: kaydır ya da sol / sağa dokun",
                 "Mavi pad'ler: 3 saniye BOOST",
                 "M: sesi aç / kapat"]
        for i, text in enumerate(lines):
            draw_neon_text(screen, text, self.small_font, WHITE, center=(WIDTH // 2, 404 + i * 28))
        if self.high_score:
            draw_neon_text(screen, f"En iyi: {self.high_score}", self.font, YELLOW, center=(WIDTH // 2, 545))
        if (self.time // 30) % 2 == 0:
            draw_neon_text(screen, "SPACE veya TIKLA: BAŞLA", self.font, CYAN, center=(WIDTH // 2, 590))

    def draw_game_over(self, screen):
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 140))
        screen.blit(overlay, (0, 0))
        if self.new_record:
            t = (math.sin(self.time * 0.15) + 1) / 2
            draw_neon_text(screen, "YENİ REKOR!", self.mid_font, mix(YELLOW, MAGENTA, t), center=(WIDTH // 2, 215))
        draw_neon_text(screen, "GAME OVER", self.big_font, MAGENTA, center=(WIDTH // 2, 280))
        draw_neon_text(screen, f"Skor: {int(self.score)}", self.font, WHITE, center=(WIDTH // 2, 345))
        draw_neon_text(screen, f"En iyi: {self.high_score}", self.font, YELLOW, center=(WIDTH // 2, 380))
        if (self.time // 30) % 2 == 0:
            draw_neon_text(screen, "SPACE veya TIKLA: tekrar oyna", self.font, CYAN, center=(WIDTH // 2, 440))
        self.draw_mute_button(screen)

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
