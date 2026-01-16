import pygame
from fighter import Fighter

pygame.init()

# CREATE GAME WINDOW

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600

# SET FRAME RATE
clock = pygame.time.Clock()
FPS = 60

# DEFINE COLORS
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Street Fighter")

# LOAD BACKGROUD IMAGE

bg_image = pygame.image.load(
    "multimedia/images/background/background.jpg").convert_alpha()

# DRAW BACKGROUND


def draw_bg():
    scaled_bg = pygame.transform.scale(bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    screen.blit(scaled_bg, (0, 0))

# DRAW HP


def draw_hp(health, x, y):
    ratio = health / 100
    pygame.draw.rect(screen, WHITE, (x - 2, y - 2, 404, 34))
    pygame.draw.rect(screen, RED, (x, y, 400, 30))
    pygame.draw.rect(screen, YELLOW, (x, y,  400*ratio, 30))

    # CREACT 2 INSTANCES OF FIGHTERS


figther_1 = Fighter(200, 310)
figther_2 = Fighter(700, 310)


# GAME LOOP
run = True

while run:

    clock.tick(FPS)

    # DRAW BACKGROUND
    draw_bg()

    # SHOW PLAYER HP
    draw_hp(figther_1.health, 20, 20)
    draw_hp(figther_2.health, 580, 20)

    # MOVE FIGHTERS
    figther_1.move(SCREEN_WIDTH, SCREEN_HEIGHT, screen, figther_2)

    # DRAW FIGHTERS
    figther_1.draw_fighter(screen)
    figther_2.draw_fighter(screen)

    # EVENT HANDLER
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            run = False

    # UPDATE DISPLAY
    pygame.display.update()

# EXIT PYGAME
pygame.quit()
