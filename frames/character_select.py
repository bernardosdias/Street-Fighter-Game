from characters.characters import CHARACTERS
import pygame
import os
import sys

# Adicionar o diretório pai ao path para importar CHARACTERS
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class CharacterSelectFrame:
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.anim_index = 0
        self.anim_timer = pygame.time.get_ticks()
        self.anim_speed = 100  # milliseconds between frames

        # Carregar personagens do dicionário CHARACTERS
        self.characters = self._load_characters()
        self.selected_option = 0

        # FONTS
        self.title_font = pygame.font.Font("multimedia/fonts/Turok.ttf", 60)
        self.option_font = pygame.font.Font("multimedia/fonts/Turok.ttf", 40)

    def _load_characters(self):
        """
        Carrega todas as personagens do dicionário CHARACTERS
        e prepara os seus spritesheets de idle para preview.
        """
        characters = []

        for char_name, char_data in CHARACTERS.items():
            try:
                # Obter a animação de idle
                idle_anim = char_data["animations"].get("idle")
                if not idle_anim:
                    print(
                        f"Aviso: {char_name} não tem animação 'idle', a saltar.")
                    continue

                idle_path, idle_frames = idle_anim

                # Carregar o spritesheet de idle
                full_path = os.path.join(
                    "multimedia/images", char_data["path"], idle_path)
                idle_sheet = pygame.image.load(full_path).convert_alpha()

                # Adicionar à lista de personagens
                characters.append({
                    "name": char_name,
                    "image": idle_sheet,
                    "size": char_data["size"],
                    "scale": char_data["scale"],
                    "idle_frames": idle_frames,
                    "offset": char_data["offset"]
                })

            except Exception as e:
                print(f"Erro ao carregar {char_name}: {e}")
                continue

        if not characters:
            print("ERRO: Nenhuma personagem foi carregada!")
            # Adicionar personagem de fallback
            characters.append({
                "name": "ERROR",
                "image": pygame.Surface((100, 100)),
                "size": 100,
                "scale": 1,
                "idle_frames": 1,
                "offset": [0, 0]
            })

        return characters

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_LEFT:
                    self.selected_option = (
                        self.selected_option - 1) % len(self.characters)
                    self.anim_index = 0  # Reset animation index when changing character
                    self.anim_timer = pygame.time.get_ticks()
                if event.key == pygame.K_RIGHT:
                    self.selected_option = (
                        self.selected_option + 1) % len(self.characters)
                    self.anim_index = 0  # Reset animation index when changing character
                    self.anim_timer = pygame.time.get_ticks()
                if event.key == pygame.K_RETURN:
                    return {
                        "next": "game",
                        "character": self.characters[self.selected_option]["name"]
                    }
                if event.key == pygame.K_ESCAPE:
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

        # Título
        title = self.title_font.render(
            "Select Your Fighter", True, (255, 0, 0))
        screen.blit(title, (self.screen_width //
                    2 - title.get_width() // 2, 50))

        # Desenhar nomes de todas as personagens disponíveis
        total_chars = len(self.characters)
        spacing = min(200, self.screen_width // (total_chars + 1))

        for i, character in enumerate(self.characters):
            color = (255, 255, 0) if i == self.selected_option else (
                150, 150, 150)
            txt = self.option_font.render(character["name"], True, color)

            # Posicionar os nomes horizontalmente
            x_pos = (self.screen_width // 2) - \
                ((total_chars - 1) * spacing // 2) + (i * spacing)
            screen.blit(txt, (x_pos - txt.get_width() //
                        2, self.screen_height - 100))

        # Desenhar preview da personagem selecionada
        character = self.characters[self.selected_option]

        sheet = character["image"]
        size = character["size"]
        scale = character["scale"]
        offset_x, offset_y = character.get("offset", [0, 0])

        sheet_width = sheet.get_width()
        sheet_height = sheet.get_height()
        frame_count = character["idle_frames"]

        frame_width = sheet_width // frame_count
        frame_height = sheet_height

        frame_x = self.anim_index * frame_width

        if frame_x + frame_width > sheet_width:
            self.anim_index = 0
            frame_x = 0

        # Extrair o frame atual
        frame = sheet.subsurface(frame_x, 0, frame_width, frame_height)

        # Escalar o frame
        preview_image = pygame.transform.scale(
            frame, (int(frame_width * scale), int(frame_height * scale)))
        # Centralizar na tela
        screen.blit(preview_image, (self.screen_width //
                    2 - preview_image.get_width() // 2 + offset_x, 300 - preview_image.get_height() // 2 + offset_y))
        # Nome da personagem selecionada (grande)
        name_surface = self.title_font.render(
            character["name"], True, (255, 255, 0))
        name_rect = name_surface.get_rect(
            center=(self.screen_width // 2, 450))
        screen.blit(name_surface, name_rect)

        # Instruções
        instructions_font = pygame.font.Font("multimedia/fonts/Turok.ttf", 25)
        instructions = instructions_font.render(
            "← → to select | ENTER to confirm | ESC to go back", True, (150, 150, 150))
        screen.blit(instructions, (self.screen_width // 2 - instructions.get_width() // 2,
                                   self.screen_height - 50))
