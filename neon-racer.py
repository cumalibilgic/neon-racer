import sys
import pygame

WIDTH, HEIGHT = 480, 720
ROAD_LEFT = 70
ROAD_RIGHT = WIDTH - 70
LANE_WIDTH = (ROAD_RIGHT - ROAD_LEFT) // 3
CAR_W, CAR_H = 54, 92


BG = (8, 10, 24)
ROAD = (22, 24, 38)
CYAN = (0, 230, 255)
MAGENTA = (255, 0, 200)
WHITE = (235, 240, 255)
PLAYER_COLOR = (30, 120, 255)




pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Neon Racer")
clock = pygame.time.Clock()

player = pygame.Rect(0, 0, CAR_W, CAR_H)
player.centerx = WIDTH // 2
player.bottom = HEIGHT - 40


while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()


    screen.fill(BG)
    pygame.draw.rect(screen, ROAD, (ROAD_LEFT, 0, ROAD_RIGHT - ROAD_LEFT, HEIGHT))
    pygame.draw.rect(screen, CYAN, (ROAD_LEFT - 4, 0, 4, HEIGHT))
    pygame.draw.rect(screen, MAGENTA, (ROAD_RIGHT, 0, 4, HEIGHT))
    
    for y in range(0, HEIGHT, 60):
        pygame.draw.rect(screen, WHITE, (ROAD_LEFT + LANE_WIDTH, y, 4, 34))
        pygame.draw.rect(screen, WHITE, (ROAD_LEFT + LANE_WIDTH * 2, y, 4, 34))
    pygame.draw.rect(screen, PLAYER_COLOR, player, border_radius = 10)
    
    pygame.display.flip()
    clock.tick(60)