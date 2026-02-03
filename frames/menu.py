import pygame


class MenuFrame:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.options = ["Start Game", "Exit"]
        self.selected_option = 0

        # FONTS
        self.title_font = pygame.font.Font("multimedia/fonts/Turok.ttf", 74)
        self.option_font = pygame.font.Font("multimedia/fonts/Turok.ttf", 50)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_option = (
                        self.selected_option - 1) % len(self.options)
                if event.key == pygame.K_DOWN:
                    self.selected_option = (
                        self.selected_option + 1) % len(self.options)
                if event.key == pygame.K_RETURN:
                    if self.selected_option == 0:
                        return "character_selection"
                    elif self.selected_option == 1:
                        pygame.quit()
                        exit()
        return None

    def update(self):
        pass

    def draw(self, screen):
        screen.fill((0, 0, 0))

        # Title
        title_surface = self.title_font.render(
            "Fighter Game", True, (255, 0, 0))
        title_rect = title_surface.get_rect(
            center=(self.screen_width // 2, 150))
        screen.blit(title_surface, title_rect)

        # Menu Options
        for i, option in enumerate(self.options):
            color = (255, 255, 0) if i == self.selected_option else (
                255, 255, 255)
            option_surface = self.option_font.render(option, True, color)
            option_rect = option_surface.get_rect(
                center=(self.screen_width // 2, 300 + i * 60))
            screen.blit(option_surface, option_rect)
