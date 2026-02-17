from network.protocol import MessageType
from characters.characters import CHARACTERS
import pygame
from core.assets import font_path, image_path
from fighters.animation_loader import load_animation_region


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

        self.card_size = 110
        self.gap_x = 20
        self.gap_y = 20
        self.grid_margin_x = 24
        self.grid_top = 140
        self.icon_size = 90
        self.icon_height_ratio = 0.78

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

                if isinstance(idle_anim, dict):
                    select_region = char_data.get(
                        "select_idle_region", idle_anim.get("region"))
                    select_frames = char_data.get("select_idle_frames", None)
                    idle_frames = load_animation_region(
                        char_data["path"],
                        idle_anim["sheet"],
                        1,
                        select_region,
                        select_frames,
                    )
                    icon_frames = self._build_icon_frames(idle_frames)
                else:
                    idle_path, _ = idle_anim
                    full_path = image_path(char_data["path"], idle_path)
                    idle_sheet = pygame.image.load(full_path).convert_alpha()
                    icon_frames = [self._fit_surface(
                        idle_sheet, self.icon_size, self.icon_size)]

                characters.append(
                    {
                        "name": char_name,
                        "icon_frames": icon_frames,
                        "size": char_data["size"],
                        "scale": char_data["scale"],
                        "idle_frames": len(icon_frames),
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
                    "icon_frames": [fallback],
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
                    "next": "online_map_select",
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
                        self._move_selection(-1, 0)
                        self.anim_index = 0
                        self.anim_timer = pygame.time.get_ticks()

                    elif event.key == pygame.K_RIGHT:
                        self._move_selection(1, 0)
                        self.anim_index = 0
                        self.anim_timer = pygame.time.get_ticks()

                    elif event.key == pygame.K_UP:
                        self._move_selection(0, -1)
                        self.anim_index = 0
                        self.anim_timer = pygame.time.get_ticks()

                    elif event.key == pygame.K_DOWN:
                        self._move_selection(0, 1)
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

        title = self.title_font.render(
            "Select Your Fighter", True, (255, 0, 0))
        screen.blit(title, (self.screen_width //
                    2 - title.get_width() // 2, 50))

        player_text = f"You are Player {self.player_id}"
        player_label = self.message_font.render(
            player_text, True, (255, 255, 0))
        screen.blit(player_label, (20, 20))

        self._draw_character_cards(screen)

        if self.ready:
            if self.opponent_character:
                status = "Waiting for game to start..."
                opponent_status = f"Opponent selected: {self.opponent_character}"
            else:
                status = "Waiting for opponent to select..."
                opponent_status = ""
        else:
            status = "ARROWS to select | ENTER to confirm"
            if self.opponent_character:
                opponent_status = f"Opponent selected: {self.opponent_character}"
            else:
                opponent_status = "Opponent is selecting..."

        status_label = self.message_font.render(status, True, (200, 200, 200))
        screen.blit(status_label, (self.screen_width //
                    2 - status_label.get_width() // 2, 520))

        if opponent_status:
            opp_label = self.message_font.render(
                opponent_status, True, (100, 200, 255))
            screen.blit(opp_label, (self.screen_width //
                        2 - opp_label.get_width() // 2, 550))

        esc_label = self.message_font.render(
            "ESC to disconnect", True, (150, 150, 150))
        screen.blit(
            esc_label,
            (self.screen_width // 2 - esc_label.get_width() //
             2, self.screen_height - 25),
        )

    def _grid_cols(self):
        usable_width = self.screen_width - (2 * self.grid_margin_x)
        cell_w = self.card_size + self.gap_x
        return max(1, (usable_width + self.gap_x) // cell_w)

    def _move_selection(self, dx, dy):
        total = len(self.characters)
        if total == 0:
            return

        cols = self._grid_cols()
        row = self.selected_option // cols
        col = self.selected_option % cols

        if dx != 0:
            self.selected_option = (self.selected_option + dx) % total
            return

        if dy != 0:
            target_row = row + dy
            target_index = target_row * cols + col
            if 0 <= target_index < total:
                self.selected_option = target_index

    def _draw_character_cards(self, screen):
        cols = self._grid_cols()
        start_x = self.grid_margin_x
        start_y = self.grid_top

        for i, character in enumerate(self.characters):
            row = i // cols
            col = i % cols
            x = start_x + col * (self.card_size + self.gap_x)
            y = start_y + row * (self.card_size + self.gap_y)
            frame_image = self._get_character_icon(
                character, i == self.selected_option)

            card_rect = pygame.Rect(
                x,
                y,
                self.card_size,
                self.card_size,
            )

            if self.ready and i == self.selected_option:
                border_color = (0, 255, 0)
            elif i == self.selected_option:
                border_color = (255, 255, 0)
            else:
                border_color = (100, 100, 100)

            pygame.draw.rect(screen, (30, 30, 30), card_rect, border_radius=8)
            pygame.draw.rect(screen, border_color,
                             card_rect, 3, border_radius=8)
            icon_rect = frame_image.get_rect(center=card_rect.center)
            screen.blit(frame_image, icon_rect)

    def _get_character_icon(self, character, selected):
        frames = character["icon_frames"]
        if not frames:
            return pygame.Surface((self.icon_size, self.icon_size), pygame.SRCALPHA)
        if selected:
            return frames[self.anim_index % len(frames)]
        return frames[0]

    def _build_icon_frames(self, frames):
        if not frames:
            fallback = pygame.Surface(
                (self.icon_size, self.icon_size), pygame.SRCALPHA)
            return [fallback]

        return [self._fit_surface(frame, self.icon_size, self.icon_size) for frame in frames]

    def _fit_surface(self, surface, box_w, box_h):
        w, h = surface.get_width(), surface.get_height()
        if w <= 0 or h <= 0:
            return pygame.Surface((box_w, box_h), pygame.SRCALPHA)

        target_box_h = int(box_h * self.icon_height_ratio)
        scale = min(box_w / float(w), target_box_h / float(h))
        target_w = max(1, int(w * scale))
        target_h = max(1, int(h * scale))
        scaled = pygame.transform.smoothscale(surface, (target_w, target_h))

        out = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        out.blit(scaled, ((box_w - target_w) // 2, (box_h - target_h) // 2))
        return out
