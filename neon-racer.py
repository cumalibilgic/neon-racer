import sys
import pygame

WIDTH, HEIGHT = 480, 720
ROAD_LEFT = 70
ROAD_RIGHT = WIDTH - 70

BG = (8, 10, 24)
ROAD = (22, 24, 38)
CYAN = (0, 230, 255)
MAGENTA = (255, 0, 200)



pygame.init()
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Neon Racer")
clock = pygame.time.Clock()

while True:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()


    screen.fill(BG)
    pygame.draw.rect(screen, ROAD, (ROAD_LEFT, 0, ROAD_RIGHT - ROAD_LEFT, HEIGHT))
    pygame.draw.rect(screen, CYAN, (ROAD_LEFT - 4, 0, 4, HEIGHT))
    pygame.draw.rect(screen, MAGENTA, (ROAD_RIGHT, 0, 4, HEIGHT))
    pygame.display.flip()
    clock.tick(60)