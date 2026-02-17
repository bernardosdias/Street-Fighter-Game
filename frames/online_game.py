import pygame
from characters.characters import CHARACTERS
from fighters.fighter import Fighter
from network.protocol import MessageType, create_player_state_update_message
from core.assets import audio_path, font_path, image_path
from core.animated_background import AnimatedBackground


class OnlineGameFrame:
    """Game frame para multiplayer online"""

    def __init__(self, width, height, client, player_id, player1_character, player2_character, is_host, map_path=None):
        self.width = width
        self.height = height
        self.client = client
        self.player_id = player_id
        self.is_host = is_host
        self.map_path = map_path

        self.ground_y = self.height - 110

        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.YELLOW = (255, 255, 0)

        self.intro_count = 3
        self.last_count_update = pygame.time.get_ticks()
        self.score = [0, 0]
        self.round_over = False

        self._load_assets()

        self.fighter1 = Fighter(
            player=1,
            x=200,
            y=self.ground_y,
            flip=False,
            character_name=player1_character,
            sound=self._get_character_sound(player1_character),
        )

        self.fighter2 = Fighter(
            player=2,
            x=700,
            y=self.ground_y,
            flip=True,
            character_name=player2_character,
            sound=self._get_character_sound(player2_character),
        )

        if self.player_id == 1:
            self.my_fighter = self.fighter1
            self.opponent_fighter = self.fighter2
        else:
            self.my_fighter = self.fighter2
            self.opponent_fighter = self.fighter1

        self.last_state_send = pygame.time.get_ticks()
        self.state_send_interval = 50
        self.last_hit_sent = 0
        self.hit_cooldown = 500
        self.hit_sent_this_attack = False
        self.disconnected = False

    def _get_character_sound(self, character_name):
        if character_name not in CHARACTERS:
            return self.default_sound

        sound_file = CHARACTERS[character_name].get(
            "attack_sound", "sword.wav")
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
        self.victory_image = pygame.image.load(
            image_path("icons", "victory.png")).convert_alpha()

        self.count_font = pygame.font.Font(font_path(), 80)
        self.score_font = pygame.font.Font(font_path(), 30)
        self.info_font = pygame.font.Font(font_path(), 20)

    def handle_events(self, events):
        if self.disconnected:
            return {"next": "menu"}

        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                self.client.disconnect()
                return {"next": "menu"}

        return None

    def update(self):
        self.background.update()

        while self.client.has_messages():
            msg = self.client.get_message()

            if msg.msg_type == MessageType.PLAYER_STATE_UPDATE:
                opponent_id = msg.data.get("player_id")
                if opponent_id != self.player_id:
                    self._apply_opponent_state(msg.data.get("state"))

            elif msg.msg_type == MessageType.GAME_STATE_UPDATE:
                self._apply_game_state(msg.data)

            elif msg.msg_type == MessageType.DISCONNECT:
                self.disconnected = True
                self.client.disconnect()
                return

        if self.intro_count > 0:
            if pygame.time.get_ticks() - self.last_count_update >= 1000:
                self.intro_count -= 1
                self.last_count_update = pygame.time.get_ticks()

        if self.intro_count <= 0:
            self.my_fighter.move(
                self.width,
                self.height,
                None,
                self.opponent_fighter,
                self.round_over,
                apply_damage=False,
            )

            if self.my_fighter.attacking:
                now = pygame.time.get_ticks()
                if (
                    not self.hit_sent_this_attack
                    and now - self.last_hit_sent >= self.hit_cooldown
                    and self._check_attack_hit()
                ):
                    self._send_hit_message()
                    self.last_hit_sent = now
                    self.hit_sent_this_attack = True
            else:
                # Nova janela de ataque: permitir enviar hit novamente.
                self.hit_sent_this_attack = False

        self.fighter1.update()
        self.fighter2.update()

        now = pygame.time.get_ticks()
        if now - self.last_state_send >= self.state_send_interval:
            self._send_my_state()
            self.last_state_send = now

    def _send_my_state(self):
        state = {
            "x": self.my_fighter.rect.x,
            "y": self.my_fighter.rect.y,
            "action": self.my_fighter.action,
            "frame_index": self.my_fighter.frame_index,
            "flip": self.my_fighter.flip,
            "attacking": self.my_fighter.attacking,
            "vel_y": self.my_fighter.vel_y,
            "jump": self.my_fighter.jump,
            "running": self.my_fighter.running,
            "defending": self.my_fighter.defending,
        }

        msg = create_player_state_update_message(self.player_id, state)
        self.client.send_message(msg)

    def _check_attack_hit(self):
        attack_range = self.my_fighter.character_data.get("attack_range", 2.0)

        attacking_rect = pygame.Rect(
            self.my_fighter.rect.centerx
            - (attack_range * self.my_fighter.rect.width * self.my_fighter.flip),
            self.my_fighter.rect.y,
            attack_range * self.my_fighter.rect.width,
            self.my_fighter.rect.height,
        )

        return attacking_rect.colliderect(self.opponent_fighter.rect)

    def _send_hit_message(self):
        from network.protocol import create_hit_message

        opponent_id = 2 if self.player_id == 1 else 1
        damage = 10
        msg = create_hit_message(self.player_id, opponent_id, damage)
        self.client.send_message(msg)

    def _apply_game_state(self, state):
        if not state:
            return

        self.fighter1.health = state.get(
            "player1_health", self.fighter1.health)
        self.fighter2.health = state.get(
            "player2_health", self.fighter2.health)

        score = state.get("score")
        if isinstance(score, list) and len(score) == 2:
            self.score = score

        self.round_over = bool(state.get("round_over", self.round_over))

        if state.get("reset_round"):
            self._reset_round()

    def _apply_opponent_state(self, state):
        if not state:
            return

        self.opponent_fighter.rect.x = state.get(
            "x", self.opponent_fighter.rect.x)
        self.opponent_fighter.rect.y = state.get(
            "y", self.opponent_fighter.rect.y)
        self.opponent_fighter.action = state.get(
            "action", self.opponent_fighter.action)
        self.opponent_fighter.frame_index = state.get(
            "frame_index", self.opponent_fighter.frame_index
        )
        self.opponent_fighter.flip = state.get(
            "flip", self.opponent_fighter.flip)
        self.opponent_fighter.attacking = state.get(
            "attacking", self.opponent_fighter.attacking
        )
        self.opponent_fighter.vel_y = state.get(
            "vel_y", self.opponent_fighter.vel_y)
        self.opponent_fighter.jump = state.get(
            "jump", self.opponent_fighter.jump)
        self.opponent_fighter.running = state.get(
            "running", self.opponent_fighter.running)
        self.opponent_fighter.defending = state.get(
            "defending", self.opponent_fighter.defending
        )

        if self.opponent_fighter.action < len(self.opponent_fighter.animation_list):
            anim = self.opponent_fighter.animation_list[self.opponent_fighter.action]
            if self.opponent_fighter.frame_index < len(anim):
                self.opponent_fighter.image = anim[self.opponent_fighter.frame_index]

    def _reset_round(self):
        self.round_over = False
        self.intro_count = 3

        char1 = self.fighter1.character_name
        char2 = self.fighter2.character_name

        self.fighter1 = Fighter(
            player=1,
            x=200,
            y=self.ground_y,
            flip=False,
            character_name=char1,
            sound=self._get_character_sound(char1),
        )

        self.fighter2 = Fighter(
            player=2,
            x=700,
            y=self.ground_y,
            flip=True,
            character_name=char2,
            sound=self._get_character_sound(char2),
        )

        if self.player_id == 1:
            self.my_fighter = self.fighter1
            self.opponent_fighter = self.fighter2
        else:
            self.my_fighter = self.fighter2
            self.opponent_fighter = self.fighter1

    def draw(self, screen):
        self.background.draw(screen)

        self.draw_hp(screen, self.fighter1.health, 20, 20)
        self.draw_hp(screen, self.fighter2.health, 580, 20)

        self.draw_game_wins(screen, self.score[0], 40, 80, direction=1)
        self.draw_game_wins(
            screen, self.score[1], self.width - 40, 80, direction=-1)

        self.fighter1.draw_fighter(screen)
        self.fighter2.draw_fighter(screen)

        if self.intro_count > 0:
            txt = self.count_font.render(
                str(self.intro_count), True, (255, 0, 0))
            screen.blit(
                txt, (self.width // 2 - txt.get_width() // 2, self.height // 3))

        if self.round_over:
            screen.blit(self.victory_image, (360, 150))

        latency = self.client.get_latency()
        info_text = f"Player {self.player_id} | Ping: {latency:.0f}ms"
        info_surface = self.info_font.render(info_text, True, (200, 200, 200))
        screen.blit(info_surface, (10, self.height - 30))

        esc_text = "ESC to disconnect"
        esc_surface = self.info_font.render(esc_text, True, (150, 150, 150))
        screen.blit(esc_surface, (self.width -
                    esc_surface.get_width() - 10, self.height - 30))

    def draw_hp(self, screen, hp, x, y):
        ratio = hp / 100
        pygame.draw.rect(screen, self.WHITE, (x - 2, y - 2, 404, 34))
        pygame.draw.rect(screen, self.RED, (x, y, 400, 30))
        pygame.draw.rect(screen, self.YELLOW, (x, y, 400 * ratio, 30))

    def draw_game_wins(self, screen, wins, x_start, y, radius=12, spacing=40, direction=1):
        for i in range(wins):
            x = x_start + (i * spacing * direction)
            pygame.draw.circle(screen, self.YELLOW, (x, y), radius)
