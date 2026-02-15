import pygame
from core.assets import font_path
from core.maps import discover_maps
from network.protocol import MessageType, create_map_select_message


class OnlineMapSelectFrame:
    def __init__(self, screen_width, screen_height, client, player_id, is_host, player1_character, player2_character):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.client = client
        self.player_id = player_id
        self.is_host = is_host
        self.player1_character = player1_character
        self.player2_character = player2_character

        self.maps = self._load_maps()
        self.selected_option = 0
        self.waiting_for_server = False

        self.title_font = pygame.font.Font(font_path(), 60)
        self.message_font = pygame.font.Font(font_path(), 25)
        self.thumb_w = 220
        self.thumb_h = 130
        self.thumb_gap_x = 24
        self.thumb_gap_y = 20
        self.grid_margin_x = 24
        self.grid_top = 120

    def _load_maps(self):
        maps = []
        for map_data in discover_maps():
            try:
                img = pygame.image.load(map_data["path"]).convert_alpha()
            except Exception:
                img = pygame.Surface((320, 180))
                img.fill((40, 40, 40))

            maps.append({
                "id": map_data["id"],
                "name": map_data["name"],
                "path": map_data["path"],
                "image": img,
            })
        return maps

    def _get_map_by_id(self, map_id):
        for map_data in self.maps:
            if map_data["id"] == map_id:
                return map_data
        return self.maps[0]

    def handle_events(self, events):
        while self.client.has_messages():
            msg = self.client.get_message()

            if msg.msg_type == MessageType.MAP_SELECTED:
                map_id = msg.data.get("map_id")
                selected_map = self._get_map_by_id(map_id)
                return {
                    "next": "online_game",
                    "client": self.client,
                    "player_id": self.player_id,
                    "player1_character": self.player1_character,
                    "player2_character": self.player2_character,
                    "is_host": self.is_host,
                    "map_path": selected_map["path"],
                }

            if msg.msg_type == MessageType.DISCONNECT:
                self.client.disconnect()
                return {"next": "menu"}

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.client.disconnect()
                    return {"next": "menu"}

                if not self.is_host or self.waiting_for_server:
                    continue

                if event.key == pygame.K_LEFT:
                    self._move_selection(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    self._move_selection(1, 0)
                elif event.key == pygame.K_UP:
                    self._move_selection(0, -1)
                elif event.key == pygame.K_DOWN:
                    self._move_selection(0, 1)
                elif event.key == pygame.K_RETURN:
                    selected = self.maps[self.selected_option]
                    self.client.send_message(create_map_select_message(selected["id"]))
                    self.waiting_for_server = True

        return None

    def update(self):
        pass

    def _grid_cols(self):
        usable_width = self.screen_width - (2 * self.grid_margin_x)
        cell_width = self.thumb_w + self.thumb_gap_x
        return max(1, (usable_width + self.thumb_gap_x) // cell_width)

    def _move_selection(self, dx, dy):
        total = len(self.maps)
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

    def _draw_map_cards(self, screen):
        total = len(self.maps)
        if total == 0:
            return

        cols = self._grid_cols()
        start_x = self.grid_margin_x
        start_y = self.grid_top

        for i, map_data in enumerate(self.maps):
            row = i // cols
            col = i % cols
            x = start_x + col * (self.thumb_w + self.thumb_gap_x)
            y = start_y + row * (self.thumb_h + self.thumb_gap_y)
            card_rect = pygame.Rect(x, y, self.thumb_w, self.thumb_h)
            border_color = (255, 255, 0) if i == self.selected_option else (100, 100, 100)

            thumb = pygame.transform.smoothscale(map_data["image"], (self.thumb_w, self.thumb_h))
            screen.blit(thumb, card_rect)
            pygame.draw.rect(screen, border_color, card_rect, 4, border_radius=8)

    def draw(self, screen):
        screen.fill((20, 20, 20))

        title = self.title_font.render("Select Stage", True, (255, 0, 0))
        screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 40))

        self._draw_map_cards(screen)

        if self.is_host:
            status = "ARROWS to select | ENTER to confirm"
            if self.waiting_for_server:
                status = "Sending stage selection..."
        else:
            status = "Waiting for host to select stage..."

        label = self.message_font.render(status, True, (170, 170, 170))
        screen.blit(label, (self.screen_width // 2 - label.get_width() // 2, self.screen_height - 35))
