import random
import sys
import pygame

WIDTH, HEIGHT = 480, 720
FPS = 60

ROAD_LEFT = 70
ROAD_RIGHT = WIDTH - 70
LANE_WIDTH = (ROAD_RIGHT - ROAD_LEFT) // 3
LANES = [ROAD_LEFT + LANE_WIDTH // 2,
         ROAD_LEFT + LANE_WIDTH + LANE_WIDTH // 2,
         ROAD_LEFT + LANE_WIDTH * 2 + LANE_WIDTH // 2]

CAR_W, CAR_H = 54, 92
START_SPEED = 6
MAX_SPEED = 13
BOOST_TIME = 180

BG = (8, 10, 24)
ROAD = (22, 24, 38)
CYAN = (0, 230, 255)
MAGENTA = (255, 0, 200)
WHITE = (235, 240, 255)
YELLOW = (255, 210, 60)
RED = (255, 50, 70)
DARK_GLASS = (15, 18, 30)
PLAYER_COLOR = (30, 120, 255)
TRAFFIC_COLORS = [(255, 60, 80), (255, 150, 0), (170, 70, 255), (40, 220, 140)]


def draw_glow_rect(surface, color, rect, radius=10, layers=4):
    for i in range(layers, 0, -1):
        pad = i * 4
        glow = pygame.Surface((rect.w + pad * 2, rect.h + pad * 2), pygame.SRCALPHA)
        pygame.draw.rect(glow, (*color, 22), glow.get_rect(), border_radius=radius + pad)
        surface.blit(glow, (rect.x - pad, rect.y - pad))
    pygame.draw.rect(surface, color, rect, border_radius=radius)


def draw_car(surface, rect, color):
    draw_glow_rect(surface, color, rect)
    dark = tuple(max(c - 70, 0) for c in color)
    pygame.draw.rect(surface, DARK_GLASS, (rect.x + 8, rect.y + 20, rect.w - 16, 20), border_radius=5)
    pygame.draw.rect(surface, dark, (rect.x + 10, rect.y + 42, rect.w - 20, 24), border_radius=4)
    pygame.draw.rect(surface, DARK_GLASS, (rect.x + 9, rect.y + 68, rect.w - 18, 10), border_radius=3)
    pygame.draw.rect(surface, WHITE, (rect.x + 5, rect.y + 3, 12, 5), border_radius=2)
    pygame.draw.rect(surface, WHITE, (rect.right - 17, rect.y + 3, 12, 5), border_radius=2)
    pygame.draw.rect(surface, RED, (rect.x + 5, rect.bottom - 7, 14, 4), border_radius=2)
    pygame.draw.rect(surface, RED, (rect.right - 19, rect.bottom - 7, 14, 4), border_radius=2)


def draw_text(surface, text, font, color, **position):
    image = font.render(text, True, color)
    surface.blit(image, image.get_rect(**position))


def reset_game():
    global lane, score, speed, boost, boost_timer, traffic, boost_pads
    global spawn_timer, road_offset, side_lights, game_over
    lane = 1
    score = 0
    speed = START_SPEED
    boost = False
    boost_timer = 0
    traffic = []
    boost_pads = []
    spawn_timer = 60
    road_offset = 0
    side_lights = [random.randint(0, HEIGHT) for _ in range(12)]
    game_over = False
    player.centerx = LANES[lane]


def spawn_traffic():
    busy = {car.centerx for car, _ in traffic if car.top < CAR_H * 2.5}
    new_lane = random.randrange(3)
    if LANES[new_lane] in busy or len(busy) >= 2:
        return

    car = pygame.Rect(0, 0, CAR_W, CAR_H)
    car.centerx = LANES[new_lane]
    car.bottom = 0
    traffic.append((car, random.choice(TRAFFIC_COLORS)))

    if random.random() < 0.15:
        pad_lane = random.choice([i for i in range(3) if i != new_lane])
        pad = pygame.Rect(0, 0, 50, 26)
        pad.centerx = LANES[pad_lane]
        pad.bottom = -40
        boost_pads.append(pad)


pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Neon Racer")
clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 22, bold=True)
big_font = pygame.font.SysFont("consolas", 44, bold=True)

player = pygame.Rect(0, 0, CAR_W, CAR_H)
player.bottom = HEIGHT - 40
high_score = 0
reset_game()


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            if game_over:
                if event.key in (pygame.K_r, pygame.K_SPACE):
                    reset_game()
            else:
                if event.key in (pygame.K_LEFT, pygame.K_a) and lane > 0:
                    lane -= 1
                if event.key in (pygame.K_RIGHT, pygame.K_d) and lane < 2:
                    lane += 1

    if not game_over:
        base_speed = min(START_SPEED + score / 1500, MAX_SPEED)
        if boost:
            boost_timer -= 1
            if boost_timer <= 0:
                boost = False
        speed = base_speed * 1.5 if boost else base_speed

        diff = LANES[lane] - player.centerx
        if abs(diff) < 3:
            player.centerx = LANES[lane]
        else:
            player.centerx += round(diff * 0.25)

        spawn_timer -= 1
        if spawn_timer <= 0:
            spawn_traffic()
            spawn_timer = int(max(15, random.randint(35, 70) * START_SPEED / speed))

        for car, _ in traffic:
            car.y += speed
        for pad in boost_pads:
            pad.y += speed
        traffic = [(car, color) for car, color in traffic if car.top < HEIGHT]
        boost_pads = [pad for pad in boost_pads if pad.top < HEIGHT]

        road_offset = (road_offset + speed) % 60
        for i in range(len(side_lights)):
            side_lights[i] += speed * 1.3
            if side_lights[i] > HEIGHT:
                side_lights[i] = random.randint(-200, -40)

        for pad in boost_pads[:]:
            if player.colliderect(pad):
                boost = True
                boost_timer = BOOST_TIME
                boost_pads.remove(pad)

        score += speed * 0.1

        hitbox = player.inflate(-12, -14)
        for car, _ in traffic:
            if hitbox.colliderect(car):
                game_over = True
                high_score = max(high_score, int(score))
                break

    screen.fill(BG)

    for i, y in enumerate(side_lights):
        x = 22 if i % 2 == 0 else WIDTH - 28
        pygame.draw.rect(screen, YELLOW, (x, int(y), 6, 40), border_radius=3)

    pygame.draw.rect(screen, ROAD, (ROAD_LEFT, 0, ROAD_RIGHT - ROAD_LEFT, HEIGHT))
    draw_glow_rect(screen, CYAN, pygame.Rect(ROAD_LEFT - 4, 0, 4, HEIGHT), radius=2, layers=3)
    draw_glow_rect(screen, MAGENTA, pygame.Rect(ROAD_RIGHT, 0, 4, HEIGHT), radius=2, layers=3)

    for y in range(int(road_offset) - 60, HEIGHT, 60):
        pygame.draw.rect(screen, WHITE, (ROAD_LEFT + LANE_WIDTH, y, 4, 34), border_radius=2)
        pygame.draw.rect(screen, WHITE, (ROAD_LEFT + LANE_WIDTH * 2, y, 4, 34), border_radius=2)

    for pad in boost_pads:
        draw_glow_rect(screen, CYAN, pad, radius=6, layers=3)
        for dx in (-10, 10):
            cx = pad.centerx + dx
            pygame.draw.polygon(screen, BG, [(cx - 7, pad.bottom - 6), (cx, pad.top + 6), (cx + 7, pad.bottom - 6)])

    for car, color in traffic:
        draw_car(screen, car, color)
    draw_car(screen, player, CYAN if boost else PLAYER_COLOR)

    draw_text(screen, "NEON RACER", font, CYAN, topleft=(12, 10))
    draw_text(screen, f"SCORE: {int(score)}", font, WHITE, topright=(WIDTH - 12, 10))
    draw_text(screen, f"SPEED: {int(speed * 18)}", font, WHITE, topright=(WIDTH - 12, 36))
    if boost:
        draw_text(screen, "BOOST!", font, YELLOW, topleft=(12, 36))
        pygame.draw.rect(screen, YELLOW, (12, 64, int(100 * boost_timer / BOOST_TIME), 6), border_radius=3)

    if game_over:
        overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 170))
        screen.blit(overlay, (0, 0))
        draw_text(screen, "GAME OVER", big_font, MAGENTA, center=(WIDTH // 2, HEIGHT // 2 - 60))
        draw_text(screen, f"Skor: {int(score)}", font, WHITE, center=(WIDTH // 2, HEIGHT // 2))
        draw_text(screen, f"En iyi: {high_score}", font, YELLOW, center=(WIDTH // 2, HEIGHT // 2 + 32))
        draw_text(screen, "R / SPACE: tekrar oyna", font, CYAN, center=(WIDTH // 2, HEIGHT // 2 + 80))

    pygame.display.flip()
    clock.tick(FPS)