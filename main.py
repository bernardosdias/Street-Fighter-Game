import pygame
from fighters.fighter import Fighter
from pygame import mixer
from frames.menu import MenuFrame
from frames.game import GameFrame
from frames.character_select import CharacterSelectFrame

# mixer.init()
pygame.init()

# CREATE GAME WINDOW

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600

# SET FRAME RATE
FPS = 60

clock = pygame.time.Clock()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

# CREATE MENU FRAME
current_frame = MenuFrame(SCREEN_WIDTH, SCREEN_HEIGHT)

# GAME LOOP
run = True

while run:

    clock.tick(FPS)

    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            run = False

    next_frame = current_frame.handle_events(events)

    if next_frame:
        if next_frame["next"] == "menu":
            current_frame = MenuFrame(SCREEN_WIDTH, SCREEN_HEIGHT)
        elif next_frame["next"] == "character_select":
            current_frame = CharacterSelectFrame(SCREEN_WIDTH, SCREEN_HEIGHT)
        elif next_frame["next"] == "game":
            character = next_frame.get("character", "Warrior")
            current_frame = GameFrame(
                SCREEN_WIDTH, SCREEN_HEIGHT, player1_character=character)

    current_frame.update()
    current_frame.draw(screen)

    pygame.display.update()

# EXIT PYGAME
pygame.quit()
