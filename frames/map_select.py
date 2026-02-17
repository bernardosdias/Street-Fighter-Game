import pygame
from core.assets import font_path
from core.maps import discover_maps


class MapSelectFrame:
    def __init__(self, screen_width, screen_height, character):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.character = character
        self.maps = self._load_maps()
        self.selected_option = 0

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

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self._move_selection(-1, 0)
                elif event.key == pygame.K_RIGHT:
                    self._move_selection(1, 0)
                elif event.key == pygame.K_UP:
                    self._move_selection(0, -1)
                elif event.key == pygame.K_DOWN:
                    self._move_selection(0, 1)
                elif event.key == pygame.K_RETURN:
                    selected_map = self.maps[self.selected_option]
                    return {
                        "next": "game",
                        "character": self.character,
                        "map_path": selected_map["path"],
                    }
                elif event.key == pygame.K_ESCAPE:
                    return {"next": "character_select"}
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
            border_color = (255, 255, 0) if i == self.selected_option else (
                100, 100, 100)

            thumb = pygame.transform.smoothscale(
                map_data["image"], (self.thumb_w, self.thumb_h))
            screen.blit(thumb, card_rect)
            pygame.draw.rect(screen, border_color,
                             card_rect, 4, border_radius=8)

    def draw(self, screen):
        screen.fill((20, 20, 20))

        title = self.title_font.render("Select Stage", True, (255, 0, 0))
        screen.blit(title, (self.screen_width //
                    2 - title.get_width() // 2, 40))

        self._draw_map_cards(screen)

        controls = self.message_font.render(
            "ARROWS to select | ENTER to confirm | ESC to go back",
            True,
            (160, 160, 160),
        )
        screen.blit(
            controls,
            (self.screen_width // 2 - controls.get_width() //
             2, self.screen_height - 35),
        )
