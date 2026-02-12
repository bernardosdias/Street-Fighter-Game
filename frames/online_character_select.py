from network.protocol import MessageType
from characters.characters import CHARACTERS
import pygame
from core.assets import font_path, image_path


class OnlineCharacterSelectFrame:
    """Character select sincronizado pela rede"""

    def __init__(self, screen_width, screen_height, client, player_id, is_host):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.client = client
        self.player_id = player_id
        self.is_host = is_host

        self.anim_index = 0
        self.anim_timer = pygame.time.get_ticks()
        self.anim_speed = 100

        self.characters = self._load_characters()
        self.selected_option = 0

        self.my_character = None
        self.opponent_character = None
        self.ready = False

        self.title_font = pygame.font.Font(font_path(), 60)
        self.option_font = pygame.font.Font(font_path(), 40)
        self.message_font = pygame.font.Font(font_path(), 25)

    def _load_characters(self):
        characters = []

        for char_name, char_data in CHARACTERS.items():
            try:
                idle_anim = char_data["animations"].get("idle")
                if not idle_anim:
                    continue

                idle_path, idle_frames = idle_anim
                full_path = image_path(char_data["path"], idle_path)
                idle_sheet = pygame.image.load(full_path).convert_alpha()

                characters.append(
                    {
                        "name": char_name,
                        "image": idle_sheet,
                        "size": char_data["size"],
                        "scale": char_data["scale"],
                        "idle_frames": idle_frames,
                        "offset": char_data["offset"],
                    }
                )
            except Exception as e:
                print(f"Erro ao carregar {char_name}: {e}")
                continue

        if not characters:
            fallback = pygame.Surface((100, 100))
            fallback.fill((255, 0, 255))
            characters.append(
                {
                    "name": "ERROR",
                    "image": fallback,
                    "size": 100,
                    "scale": 1,
                    "idle_frames": 1,
                    "offset": [0, 0],
                }
            )

        return characters

    def handle_events(self, events):
        while self.client.has_messages():
            msg = self.client.get_message()

            if msg.msg_type == MessageType.CHARACTER_SELECTED:
                opponent_char = msg.data.get("character")
                self.opponent_character = opponent_char

            elif msg.msg_type == MessageType.BOTH_READY:
                p1_char = msg.data.get("player1_character")
                p2_char = msg.data.get("player2_character")
                return {
                    "next": "online_game",
                    "client": self.client,
                    "player_id": self.player_id,
                    "player1_character": p1_char,
                    "player2_character": p2_char,
                    "is_host": self.is_host,
                }

        for event in events:
            if event.type == pygame.KEYDOWN:
                if not self.ready:
                    if event.key == pygame.K_LEFT:
                        self.selected_option = (self.selected_option - 1) % len(self.characters)
                        self.anim_index = 0
                        self.anim_timer = pygame.time.get_ticks()

                    elif event.key == pygame.K_RIGHT:
                        self.selected_option = (self.selected_option + 1) % len(self.characters)
                        self.anim_index = 0
                        self.anim_timer = pygame.time.get_ticks()

                    elif event.key == pygame.K_RETURN:
                        self.my_character = self.characters[self.selected_option]["name"]
                        self.ready = True
                        self.client.select_character(self.my_character)

                if event.key == pygame.K_ESCAPE:
                    self.client.disconnect()
                    return {"next": "menu"}

        return None

    def update(self):
        now = pygame.time.get_ticks()
        character = self.characters[self.selected_option]

        if now - self.anim_timer >= self.anim_speed:
            self.anim_index += 1
            if self.anim_index >= character["idle_frames"]:
                self.anim_index = 0
            self.anim_timer = now

    def draw(self, screen):
        screen.fill((20, 20, 20))

        title = self.title_font.render("Select Your Fighter", True, (255, 0, 0))
        screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 50))

        player_text = f"You are Player {self.player_id}"
        player_label = self.message_font.render(player_text, True, (255, 255, 0))
        screen.blit(player_label, (20, 20))

        self._draw_character_cards(screen)

        character = self.characters[self.selected_option]
        sheet = character["image"]
        scale = character["scale"]
        offset_x, offset_y = character.get("offset", [0, 0])

        sheet_width = sheet.get_width()
        sheet_height = sheet.get_height()
        frame_count = max(1, character["idle_frames"])

        frame_width = sheet_width // frame_count
        frame_height = sheet_height

        frame_x = self.anim_index * frame_width
        if frame_x + frame_width > sheet_width:
            self.anim_index = 0
            frame_x = 0

        frame = sheet.subsurface(frame_x, 0, frame_width, frame_height)
        preview_image = pygame.transform.scale(
            frame, (int(frame_width * scale), int(frame_height * scale))
        )

        preview_x = self.screen_width // 2 - preview_image.get_width() // 2 + offset_x
        preview_y = 300 - preview_image.get_height() // 2 + offset_y
        screen.blit(preview_image, (preview_x, preview_y))

        name_surface = self.title_font.render(character["name"], True, (255, 255, 0))
        name_rect = name_surface.get_rect(center=(self.screen_width // 2, 430))
        screen.blit(name_surface, name_rect)

        if self.ready:
            if self.opponent_character:
                status = "Waiting for game to start..."
                opponent_status = f"Opponent selected: {self.opponent_character}"
            else:
                status = "Waiting for opponent to select..."
                opponent_status = ""
        else:
            status = "LEFT RIGHT to select | ENTER to confirm"
            if self.opponent_character:
                opponent_status = f"Opponent selected: {self.opponent_character}"
            else:
                opponent_status = "Opponent is selecting..."

        status_label = self.message_font.render(status, True, (200, 200, 200))
        screen.blit(status_label, (self.screen_width // 2 - status_label.get_width() // 2, 510))

        if opponent_status:
            opp_label = self.message_font.render(opponent_status, True, (100, 200, 255))
            screen.blit(opp_label, (self.screen_width // 2 - opp_label.get_width() // 2, 540))

        esc_label = self.message_font.render("ESC to disconnect", True, (150, 150, 150))
        screen.blit(
            esc_label,
            (self.screen_width // 2 - esc_label.get_width() // 2, self.screen_height - 30),
        )

    def _draw_character_cards(self, screen):
        total_chars = len(self.characters)
        spacing = min(120, self.screen_width // max(1, total_chars + 1))
        card_size = 86
        y_pos = self.screen_height - 155

        for i, character in enumerate(self.characters):
            x_center = (self.screen_width // 2) - ((total_chars - 1) * spacing // 2) + (i * spacing)
            frame_image = self._get_character_icon(character)

            card_rect = pygame.Rect(
                x_center - card_size // 2,
                y_pos - card_size // 2,
                card_size,
                card_size,
            )

            if self.ready and i == self.selected_option:
                border_color = (0, 255, 0)
            elif i == self.selected_option:
                border_color = (255, 255, 0)
            else:
                border_color = (100, 100, 100)

            pygame.draw.rect(screen, (30, 30, 30), card_rect, border_radius=8)
            pygame.draw.rect(screen, border_color, card_rect, 3, border_radius=8)
            icon_rect = frame_image.get_rect(center=card_rect.center)
            screen.blit(frame_image, icon_rect)

    def _get_character_icon(self, character):
        sheet = character["image"]
        frame_count = max(1, character["idle_frames"])
        frame_width = sheet.get_width() // frame_count
        frame_height = sheet.get_height()
        frame = sheet.subsurface(0, 0, frame_width, frame_height)
        return pygame.transform.smoothscale(frame, (72, 72))
