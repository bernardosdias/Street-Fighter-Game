import random
import pygame
from characters.characters import CHARACTERS
from fighters.fighter import Fighter
from core.assets import audio_path, font_path, image_path
from core.animated_background import AnimatedBackground


class GameFrame:
    def __init__(self, width, height, player1_character=None, player2_character=None, map_path=None):
        self.width = width
        self.height = height
        available_characters = list(CHARACTERS.keys())
        fallback_player1 = available_characters[0] if available_characters else "Ryu"
        fallback_player2 = (
            available_characters[1]
            if len(available_characters) > 1
            else fallback_player1
        )
        self.player1_character = player1_character or fallback_player1
        self.player2_character = player2_character or fallback_player2
        self.map_path = map_path
        self.ground_y = self.height - 110

        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.YELLOW = (255, 255, 0)

        self.clock = pygame.time.Clock()

        self.intro_count = 3
        self.last_count_update = pygame.time.get_ticks()
        self.score = [0, 0]
        self.round_over = False
        self.round_over_time = 0
        self.ai_enabled = True
        self.ai_next_decision = 0
        self.ai_controls = self._empty_ai_controls()

        self._load_assets()

        self.fighter1 = Fighter(
            player=1,
            x=200,
            y=self.ground_y,
            flip=False,
            character_name=self.player1_character,
            sound=self._get_character_sound(self.player1_character),
        )

        self.fighter2 = Fighter(
            player=2,
            x=700,
            y=self.ground_y,
            flip=True,
            character_name=self.player2_character,
            sound=self._get_character_sound(self.player2_character),
        )

    def _get_character_sound(self, character_name):
        if character_name not in CHARACTERS:
            return self.default_sound

        sound_file = CHARACTERS[character_name].get("attack_sound", "sword.wav")
        sound_path = audio_path(sound_file)

        try:
            sound = pygame.mixer.Sound(sound_path)
            sound.set_volume(0.2)
            return sound
        except Exception:
            return self.default_sound

    def _load_assets(self):
        pygame.mixer.music.load(audio_path("music.mp3"))
        pygame.mixer.music.set_volume(0.1)
        pygame.mixer.music.play(-1, 0.0, 5000)

        try:
            self.default_sound = pygame.mixer.Sound(audio_path("sword.wav"))
            self.default_sound.set_volume(0.2)
        except Exception:
            self.default_sound = pygame.mixer.Sound(buffer=bytes(100))

        bg_path = self.map_path or image_path("background", "background.jpg")
        self.background = AnimatedBackground(bg_path, self.width, self.height)
        self.victory_image = pygame.image.load(image_path("icons", "victory.png")).convert_alpha()

        self.count_font = pygame.font.Font(font_path(), 80)
        self.score_font = pygame.font.Font(font_path(), 30)

    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                return {"next": "menu"}
        return None

    def update(self):
        self.background.update()

        if self.intro_count <= 0:
            self.fighter1.move(self.width, self.height, None, self.fighter2, self.round_over)
            if self.ai_enabled:
                controls = self._get_ai_controls(self.fighter2, self.fighter1)
                self.fighter2.move(
                    self.width,
                    self.height,
                    None,
                    self.fighter1,
                    self.round_over,
                    controls=controls,
                )
            else:
                self.fighter2.move(self.width, self.height, None, self.fighter1, self.round_over)
        else:
            if pygame.time.get_ticks() - self.last_count_update >= 1000:
                self.intro_count -= 1
                self.last_count_update = pygame.time.get_ticks()

        self.fighter1.update()
        self.fighter2.update()

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

        self.draw_hp(screen, self.fighter1.health, 20, 20)
        self.draw_hp(screen, self.fighter2.health, 580, 20)

        self.draw_game_wins(screen, self.score[0], 40, 80, direction=1)
        self.draw_game_wins(screen, self.score[1], self.width - 40, 80, direction=-1)

        self.fighter1.draw_fighter(screen)
        self.fighter2.draw_fighter(screen)

        if self.intro_count > 0:
            txt = self.count_font.render(str(self.intro_count), True, (255, 0, 0))
            screen.blit(txt, (self.width // 2, self.height // 3))

        if self.round_over:
            screen.blit(self.victory_image, (360, 150))

    def _draw_bg(self, screen):
        self.background.draw(screen)

    def draw_hp(self, screen, hp, x, y):
        ratio = hp / 100
        pygame.draw.rect(screen, self.WHITE, (x - 2, y - 2, 404, 34))
        pygame.draw.rect(screen, self.RED, (x, y, 400, 30))
        pygame.draw.rect(screen, self.YELLOW, (x, y, 400 * ratio, 30))

    def draw_game_wins(self, screen, wins, x_start, y, radius=12, spacing=40, direction=1):
        for i in range(wins):
            x = x_start + (i * spacing * direction)
            if i < wins:
                pygame.draw.circle(screen, self.YELLOW, (x, y), radius)
            else:
                pygame.draw.circle(screen, self.WHITE, (x, y), radius, 2)

    def _reset_round(self):
        self.round_over = False
        self.intro_count = 3
        self.ai_controls = self._empty_ai_controls()
        self.ai_next_decision = 0

        self.fighter1 = Fighter(
            player=1,
            x=200,
            y=self.ground_y,
            flip=False,
            character_name=self.player1_character,
            sound=self._get_character_sound(self.player1_character),
        )

        self.fighter2 = Fighter(
            player=2,
            x=700,
            y=self.ground_y,
            flip=True,
            character_name=self.player2_character,
            sound=self._get_character_sound(self.player2_character),
        )

    def _empty_ai_controls(self):
        return {
            "left": False,
            "right": False,
            "jump": False,
            "attack1": False,
            "attack2": False,
        }

    def _get_ai_controls(self, ai_fighter, target_fighter):
        now = pygame.time.get_ticks()
        if now < self.ai_next_decision:
            return self.ai_controls

        controls = self._empty_ai_controls()

        distance_x = target_fighter.rect.centerx - ai_fighter.rect.centerx
        abs_distance = abs(distance_x)

        if abs_distance > 170:
            if distance_x > 0:
                controls["right"] = True
            else:
                controls["left"] = True
        elif abs_distance < 85:
            if distance_x > 0:
                controls["left"] = True
            else:
                controls["right"] = True
            if random.random() < 0.08 and not ai_fighter.jump:
                controls["jump"] = True
        else:
            if random.random() < 0.25:
                if distance_x > 0:
                    controls["right"] = True
                else:
                    controls["left"] = True

        attack_range = ai_fighter.character_data.get("attack_range", 2.0)
        attack_distance = int(ai_fighter.rect.width * attack_range * 0.75)
        can_attack = (
            abs_distance <= attack_distance
            and ai_fighter.attack_cd == 0
            and not ai_fighter.attacking
            and ai_fighter.alive
            and target_fighter.alive
        )
        if can_attack and random.random() < 0.6:
            if random.random() < 0.5:
                controls["attack1"] = True
            else:
                controls["attack2"] = True

        self.ai_controls = controls
        self.ai_next_decision = now + random.randint(90, 170)
        return self.ai_controls
