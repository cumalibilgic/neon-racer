"""Pygbag/Pygame application entry point."""

import asyncio

import pygame

from config import FPS, HEIGHT, WIDTH
from game import Game

async def main():
    # Küçük tampon bazı hoparlörlerde cızırtıya yol açıyor
    pygame.mixer.pre_init(44100, -16, 2, 2048)
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
