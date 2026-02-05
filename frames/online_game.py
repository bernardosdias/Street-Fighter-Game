import pygame
import os
import sys
from pygame import mixer

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from fighters.fighter import Fighter
from characters.characters import CHARACTERS
from network.protocol import MessageType, create_player_state_update_message


class OnlineGameFrame:
    """Game frame para multiplayer online"""
    
    def __init__(self, width, height, client, player_id, player1_character, player2_character, is_host):
        self.width = width
        self.height = height
        self.client = client
        self.player_id = player_id
        self.is_host = is_host
        
        self.ground_y = self.height - 110
        
        self.WHITE = (255, 255, 255)
        self.RED = (255, 0, 0)
        self.YELLOW = (255, 255, 0)
        
        # GAME STATE
        self.intro_count = 3
        self.last_count_update = pygame.time.get_ticks()
        self.score = [0, 0]
        self.round_over = False
        self.round_over_time = 0
        
        # LOAD ASSETS
        self._load_assets()
        
        # CREATE FIGHTERS
        self.fighter1 = Fighter(
            player=1,
            x=200,
            y=self.ground_y,
            flip=False,
            character_name=player1_character,
            sound=self._get_character_sound(player1_character)
        )
        
        self.fighter2 = Fighter(
            player=2,
            x=700,
            y=self.ground_y,
            flip=True,
            character_name=player2_character,
            sound=self._get_character_sound(player2_character)
        )
        
        # Identificar qual fighter é o local e qual é o remoto
        if self.player_id == 1:
            self.my_fighter = self.fighter1
            self.opponent_fighter = self.fighter2
        else:
            self.my_fighter = self.fighter2
            self.opponent_fighter = self.fighter1
        
        print(f"🎮 Você controla: Fighter {self.player_id}")
        
        # Network sync
        self.last_state_send = pygame.time.get_ticks()
        self.state_send_interval = 50  # Enviar estado a cada 50ms
    
    def _get_character_sound(self, character_name):
        """Retorna o som da personagem"""
        if character_name not in CHARACTERS:
            return self.default_sound
        
        sound_file = CHARACTERS[character_name].get("attack_sound", "sword.wav")
        sound_path = os.path.join("multimedia/audio", sound_file)
        
        try:
            sound = pygame.mixer.Sound(sound_path)
            sound.set_volume(0.2)
            return sound
        except:
            return self.default_sound
    
    def _load_assets(self):
        """Carrega assets"""
        # MUSIC
        pygame.mixer.music.load("multimedia/audio/music.mp3")
        pygame.mixer.music.set_volume(0.1)
        pygame.mixer.music.play(-1, 0.0, 5000)
        
        # Default sound
        try:
            self.default_sound = pygame.mixer.Sound("multimedia/audio/sword.wav")
            self.default_sound.set_volume(0.2)
        except:
            self.default_sound = pygame.mixer.Sound(buffer=bytes(100))
        
        # IMAGES
        self.bg_image = pygame.image.load(
            "multimedia/images/background/background.jpg").convert_alpha()
        self.victory_image = pygame.image.load(
            "multimedia/images/icons/victory.png").convert_alpha()
        
        # FONTS
        self.count_font = pygame.font.Font("multimedia/fonts/Turok.ttf", 80)
        self.score_font = pygame.font.Font("multimedia/fonts/Turok.ttf", 30)
        self.info_font = pygame.font.Font("multimedia/fonts/Turok.ttf", 20)
    
    def handle_events(self, events):
        """Processa eventos locais e de rede"""
        # Processar mensagens da rede
        while self.client.has_messages():
            msg = self.client.get_message()
            
            if msg.type == MessageType.PLAYER_STATE_UPDATE  :
                # Receber estado do oponente
                opponent_id = msg.data.get("player_id")
                if opponent_id != self.player_id:
                    self._apply_opponent_state(msg.data.get("state"))
            
            elif msg.type == MessageType.DISCONNECT:
                # Oponente desconectou
                print("⚠️ Oponente desconectou!")
                return "menu"
        
        # Processar eventos locais
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.client.disconnect()
                    return "menu"
        
        return None
    
    def update(self):
        """Atualiza o jogo"""
        # Atualizar intro count
        if self.intro_count > 0:
            if pygame.time.get_ticks() - self.last_count_update >= 1000:
                self.intro_count -= 1
                self.last_count_update = pygame.time.get_ticks()
        
        # Só processar movimento se o jogo começou
        if self.intro_count <= 0:
            # Atualizar MEU fighter (controle local)
            self.my_fighter.move(
                self.width, 
                self.height, 
                None, 
                self.opponent_fighter, 
                self.round_over
            )
            
            # NÃO atualizar o fighter do oponente com move()
            # Ele é atualizado via estado da rede
        
        # Atualizar animações de AMBOS
        self.fighter1.update()
        self.fighter2.update()
        
        # Enviar estado do meu fighter pela rede
        now = pygame.time.get_ticks()
        if now - self.last_state_send >= self.state_send_interval:
            self._send_my_state()
            self.last_state_send = now
        
        # Verificar round over
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
    
    def _send_my_state(self):
        """Envia o estado do meu fighter ao oponente"""
        state = {
            "x": self.my_fighter.rect.x,
            "y": self.my_fighter.rect.y,
            "health": self.my_fighter.health,
            "action": self.my_fighter.action,
            "frame_index": self.my_fighter.frame_index,
            "flip": self.my_fighter.flip,
            "attacking": self.my_fighter.attacking,
            "alive": self.my_fighter.alive,
            "vel_y": self.my_fighter.vel_y,
            "jump": self.my_fighter.jump,
            "running": self.my_fighter.running,
        }
        
        msg = create_player_state_update_message(self.player_id, state)
        self.client.send_message(msg)
    
    def _apply_opponent_state(self, state):
        """Aplica o estado recebido do oponente"""
        if not state:
            return
        
        # Atualizar posição e propriedades
        self.opponent_fighter.rect.x = state.get("x", self.opponent_fighter.rect.x)
        self.opponent_fighter.rect.y = state.get("y", self.opponent_fighter.rect.y)
        self.opponent_fighter.health = state.get("health", self.opponent_fighter.health)
        self.opponent_fighter.action = state.get("action", self.opponent_fighter.action)
        self.opponent_fighter.frame_index = state.get("frame_index", self.opponent_fighter.frame_index)
        self.opponent_fighter.flip = state.get("flip", self.opponent_fighter.flip)
        self.opponent_fighter.attacking = state.get("attacking", self.opponent_fighter.attacking)
        self.opponent_fighter.alive = state.get("alive", self.opponent_fighter.alive)
        self.opponent_fighter.vel_y = state.get("vel_y", self.opponent_fighter.vel_y)
        self.opponent_fighter.jump = state.get("jump", self.opponent_fighter.jump)
        self.opponent_fighter.running = state.get("running", self.opponent_fighter.running)
        
        # Atualizar imagem baseado na action e frame_index
        if self.opponent_fighter.action < len(self.opponent_fighter.animation_list):
            anim = self.opponent_fighter.animation_list[self.opponent_fighter.action]
            if self.opponent_fighter.frame_index < len(anim):
                self.opponent_fighter.image = anim[self.opponent_fighter.frame_index]
    
    def _reset_round(self):
        """Reseta a ronda"""
        self.round_over = False
        self.intro_count = 3
        
        # Recriar fighters
        char1 = self.fighter1.character_name
        char2 = self.fighter2.character_name
        
        self.fighter1 = Fighter(
            player=1,
            x=200,
            y=self.ground_y,
            flip=False,
            character_name=char1,
            sound=self._get_character_sound(char1)
        )
        
        self.fighter2 = Fighter(
            player=2,
            x=700,
            y=self.ground_y,
            flip=True,
            character_name=char2,
            sound=self._get_character_sound(char2)
        )
        
        # Reatribuir my_fighter e opponent_fighter
        if self.player_id == 1:
            self.my_fighter = self.fighter1
            self.opponent_fighter = self.fighter2
        else:
            self.my_fighter = self.fighter2
            self.opponent_fighter = self.fighter1
    
    def draw(self, screen):
        """Desenha o jogo"""
        # Background
        bg = pygame.transform.scale(self.bg_image, (self.width, self.height))
        screen.blit(bg, (0, 0))
        
        # Health bars
        self.draw_hp(screen, self.fighter1.health, 20, 20)
        self.draw_hp(screen, self.fighter2.health, 580, 20)
        
        # Score
        self.draw_game_wins(screen, self.score[0], 20, 80)
        self.draw_game_wins(screen, self.score[1], 690, 80)
        
        # Fighters
        self.fighter1.draw_fighter(screen)
        self.fighter2.draw_fighter(screen)
        
        # Intro count
        if self.intro_count > 0:
            txt = self.count_font.render(str(self.intro_count), True, (255, 0, 0))
            screen.blit(txt, (self.width // 2 - txt.get_width() // 2, self.height // 3))
        
        # Victory
        if self.round_over:
            screen.blit(self.victory_image, (360, 150))
        
        # Info de conexão
        latency = self.client.get_latency()
        info_text = f"Player {self.player_id} | Ping: {latency:.0f}ms"
        info_surface = self.info_font.render(info_text, True, (200, 200, 200))
        screen.blit(info_surface, (10, self.height - 30))
        
        # ESC para sair
        esc_text = "ESC to disconnect"
        esc_surface = self.info_font.render(esc_text, True, (150, 150, 150))
        screen.blit(esc_surface, (self.width - esc_surface.get_width() - 10, self.height - 30))
    
    def draw_hp(self, screen, hp, x, y):
        """Desenha barra de vida"""
        ratio = hp / 100
        pygame.draw.rect(screen, self.WHITE, (x-2, y-2, 404, 34))
        pygame.draw.rect(screen, self.RED, (x, y, 400, 30))
        pygame.draw.rect(screen, self.YELLOW, (x, y, 400 * ratio, 30))
    
    def draw_game_wins(self, screen, wins, x_start, y, radius=12, spacing=40):
        """Desenha os wins"""
        for i in range(wins):
            x = x_start + (i * spacing)
            pygame.draw.circle(screen, self.YELLOW, (x, y), radius)