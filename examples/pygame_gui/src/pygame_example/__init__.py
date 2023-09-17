def main():
    import pygame
    import random
    pygame.init()

    screen = pygame.display.set_mode([800, 600])

    running = True
    while running:

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

        screen.fill((255, 255, 255))

        pygame.draw.circle(screen, (0, 0, 255), (400, 300), random.randint(25,75))

        pygame.display.flip()

    pygame.quit()