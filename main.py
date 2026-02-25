import pygame
from frames.menu import MenuFrame
from frames.game import GameFrame
from frames.character_select import CharacterSelectFrame
from frames.map_select import MapSelectFrame
from frames.online_menu import OnlineMenuFrame
from frames.online_character_select import OnlineCharacterSelectFrame
from frames.online_map_select import OnlineMapSelectFrame
from frames.online_game import OnlineGameFrame
from characters.characters import CHARACTERS
from core.config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, WINDOW_TITLE

pygame.init()

clock = pygame.time.Clock()
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption(WINDOW_TITLE)

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
            default_character = next(iter(CHARACTERS.keys()), "Balrog")
            character = next_frame.get("character", default_character)
            map_path = next_frame.get("map_path")
            current_frame = GameFrame(
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
                player1_character=character,
                map_path=map_path,
            )

        elif next_frame["next"] == "map_select":
            current_frame = MapSelectFrame(
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
                character=next_frame["character"],
            )

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
                is_host=next_frame["is_host"],
                map_path=next_frame.get("map_path"),
            )

        elif next_frame["next"] == "online_map_select":
            current_frame = OnlineMapSelectFrame(
                SCREEN_WIDTH,
                SCREEN_HEIGHT,
                client=next_frame["client"],
                player_id=next_frame["player_id"],
                player1_character=next_frame["player1_character"],
                player2_character=next_frame["player2_character"],
                is_host=next_frame["is_host"],
            )

    current_frame.update()
    current_frame.draw(screen)

    pygame.display.update()

# EXIT PYGAME
pygame.quit()
