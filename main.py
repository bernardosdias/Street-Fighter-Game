import pygame
from fighters.fighter import Fighter
from pygame import mixer
from frames.menu import MenuFrame
from frames.game import GameFrame
from frames.character_select import CharacterSelectFrame
from frames.online_menu import OnlineMenuFrame
from frames.online_character_select import OnlineCharacterSelectFrame
from frames.online_game import OnlineGameFrame

# mixer.init()
pygame.init()

# CREATE GAME WINDOW

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600

# SET FRAME RATE
FPS = 60

clock = pygame.time.Clock()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Street Fighter - Online")

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
        
        # === ONLINE MULTIPLAYER ===
        
        elif next_frame["next"] == "online_menu":
            current_frame = OnlineMenuFrame(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        elif next_frame["next"] == "online_character_select":
            current_frame = OnlineCharacterSelectFrame(
                SCREEN_WIDTH, 
                SCREEN_HEIGHT,
                client=next_frame["client"],
                player_id=next_frame["player_id"],
                is_host=next_frame["is_host"]
            )
        
        elif next_frame["next"] == "online_game":
            current_frame = OnlineGameFrame(
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
                client=next_frame["client"],
                player_id=next_frame["player_id"],
                player1_character=next_frame["player1_character"],
                player2_character=next_frame["player2_character"],
                is_host=next_frame["is_host"]
            )

    current_frame.update()
    current_frame.draw(screen)

    pygame.display.update()

# EXIT PYGAME
pygame.quit()