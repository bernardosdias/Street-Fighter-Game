from characters.characters import CHARACTERS
from fighters.fighter import Fighter
import pygame
import os
import sys
from pygame import mixer

# Adicionar o diretório pai ao path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class GameFrame:
    def __init__(self, width, height, player1_character="Warrior", player2_character="Wizard"):
        self.width = width
        self.height = height
        self.player1_character = player1_character
        self.player2_character = player2_character
        self.ground_y = self.height - 110

        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.YELLOW = (255, 255, 0)

        # CLOCK / FPS
        self.clock = pygame.time.Clock()

        # GAME STATE
        self.intro_count = 3
        self.last_count_update = pygame.time.get_ticks()
        self.score = [0, 0]  # PLAYER SCORES. [P1, P2]
        self.round_over = False
        self.round_over_time = 0

        # LOAD ASSETS
        self._load_assets()

        # CREATE FIGHTERS usando o novo sistema!
        self.fighter1 = Fighter(
            player=1,
            x=200,
            y=self.ground_y,
            flip=False,
            character_name=self.player1_character,
            sound=self._get_character_sound(self.player1_character)
        )

        self.fighter2 = Fighter(
            player=2,
            x=700,
            y=self.ground_y,
            flip=True,
            character_name=self.player2_character,
            sound=self._get_character_sound(self.player2_character)
        )

    def _get_character_sound(self, character_name):
        """
        Carrega e retorna o som específico da personagem.
        """
        if character_name not in CHARACTERS:
            print(
                f"⚠️ Personagem '{character_name}' não encontrada, usando som padrão")
            return self.default_sound

        # Obter o nome do ficheiro de som do dicionário CHARACTERS
        sound_file = CHARACTERS[character_name].get(
            "attack_sound", "sword.wav")

        # Construir o caminho completo
        sound_path = os.path.join("multimedia/audio", sound_file)

        # Tentar carregar o som
        try:
            sound = pygame.mixer.Sound(sound_path)
            sound.set_volume(0.2)
            print(f"✅ Som carregado para {character_name}: {sound_file}")
            return sound
        except Exception as e:
            print(f"❌ Erro ao carregar som {sound_path}: {e}")
            print(f"   Usando som padrão para {character_name}")
            return self.default_sound

    def _load_assets(self):
        # LOAD MUSIC AND SOUNDS
        pygame.mixer.music.load("multimedia/audio/music.mp3")
        pygame.mixer.music.set_volume(0.1)
        pygame.mixer.music.play(-1, 0.0, 5000)

        # Carregar som padrão (fallback)
        try:
            self.default_sound = pygame.mixer.Sound(
                "multimedia/audio/sword.wav")
            self.default_sound.set_volume(0.2)
        except:
            # Se nem o sword.wav existir, criar um som silencioso
            self.default_sound = pygame.mixer.Sound(buffer=bytes(100))
            print("⚠️ Som padrão não encontrado, usando som silencioso")

        # LOAD BACKGROUND AND VICTORY IMAGES
        self.bg_image = pygame.image.load(
            "multimedia/images/background/background.jpg").convert_alpha()
        self.victory_image = pygame.image.load(
            "multimedia/images/icons/victory.png").convert_alpha()

        # FONTS
        self.count_font = pygame.font.Font("multimedia/fonts/Turok.ttf", 80)
        self.score_font = pygame.font.Font("multimedia/fonts/Turok.ttf", 30)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "menu"
        return None

    def update(self):
        if self.intro_count <= 0:
            self.fighter1.move(self.width, self.height, None,
                               self.fighter2, self.round_over)
            self.fighter2.move(self.width, self.height, None,
                               self.fighter1, self.round_over)
        else:
            if pygame.time.get_ticks() - self.last_count_update >= 1000:
                self.intro_count -= 1
                self.last_count_update = pygame.time.get_ticks()

        self.fighter1.update()
        self.fighter2.update()

        # CHECK FOR ROUND OVER
        if not self.round_over:
            if not self.fighter1.alive:
                self.score[1] += 1
                self.round_over = True
                self.round_over_time = pygame.time.get_ticks()
            elif not self.fighter2.alive:
                self.score[0] += 1
                self.round_over = True
                self.round_over_time = pygame.time.get_ticks()
        else:
            if pygame.time.get_ticks() - self.round_over_time > 2000:
                self._reset_round()

    def draw(self, screen):
        self._draw_bg(screen)

        # UI ELEMENTS
        self.draw_hp(screen, self.fighter1.health, 20, 20)
        self.draw_hp(screen, self.fighter2.health, 580, 20)

        self.draw_game_wins(screen, self.score[0], 20, 80)
        self.draw_game_wins(screen, self.score[1], 690, 80)

        self.fighter1.draw_fighter(screen)
        self.fighter2.draw_fighter(screen)

        if self.intro_count > 0:
            txt = self.count_font.render(
                str(self.intro_count), True, (255, 0, 0))
            screen.blit(txt, (self.width // 2, self.height // 3))

        if self.round_over:
            screen.blit(self.victory_image, (360, 150))

    def _draw_bg(self, screen):
        bg = pygame.transform.scale(self.bg_image, (self.width, self.height))
        screen.blit(bg, (0, 0))

    def draw_hp(self, screen, hp, x, y):
        ratio = hp / 100
        pygame.draw.rect(screen, self.WHITE, (x-2, y-2, 404, 34))
        pygame.draw.rect(screen, self.RED, (x, y, 400, 30))
        pygame.draw.rect(screen, self.YELLOW, (x, y, 400 * ratio, 30))

    def draw_game_wins(self, screen, wins, x_start, y, radius=12, spacing=40):
        for i in range(wins):
            x = x_start + (i * spacing)
            if i < wins:
                pygame.draw.circle(screen, self.YELLOW, (x, y), radius)
            else:
                pygame.draw.circle(screen, self.WHITE, (x, y), radius, 2)

    def _reset_round(self):
        """Reseta a ronda, recriando os fighters"""
        self.round_over = False
        self.intro_count = 3

        # Recriar fighters usando o novo sistema
        self.fighter1 = Fighter(
            player=1,
            x=200,
            y=self.ground_y,
            flip=False,
            character_name=self.player1_character,
            sound=self._get_character_sound(self.player1_character)
        )

        self.fighter2 = Fighter(
            player=2,
            x=700,
            y=self.ground_y,
            flip=True,
            character_name=self.player2_character,
            sound=self._get_character_sound(self.player2_character)
        )
