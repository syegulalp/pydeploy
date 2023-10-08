def main():
    import pygame

    pygame.init()

    screen = pygame.display.set_mode([800, 600])

    img = pygame.image.load("assets/image.jpg")

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
                break

        screen.fill((255, 255, 255))
        screen.blit(img, (100, 100))
        pygame.display.flip()

    pygame.quit()
