import sys
import pygame

pygame.init ()
screen = pygame.display.set_mode ((480, 720))
pygame.display.set_caption ("Neon Racer")
clock = pygame.time.Clock ()

while True:
    for event in pygame.event.get ():
        if event.type == pygame.QUIT:
            pygame.quit ()
            sys.exit ()


    screen.fill ((8, 10, 24))
    pygame.display.flip ()
    clock.tick (60)