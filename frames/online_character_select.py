import pygame
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from characters.characters import CHARACTERS
from network.protocol import MessageType


class OnlineCharacterSelectFrame:
    """Character select sincronizado pela rede"""
    
    def __init__(self, screen_width, screen_height, client, player_id, is_host):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.client = client
        self.player_id = player_id
        self.is_host = is_host
        
        # Animação
        self.anim_index = 0
        self.anim_timer = pygame.time.get_ticks()
        self.anim_speed = 100
        
        # Carregar personagens
        self.characters = self._load_characters()
        self.selected_option = 0
        
        # Estado de seleção
        self.my_character = None
        self.opponent_character = None
        self.ready = False
        
        # Fonts
        self.title_font = pygame.font.Font("multimedia/fonts/Turok.ttf", 60)
        self.option_font = pygame.font.Font("multimedia/fonts/Turok.ttf", 40)
        self.message_font = pygame.font.Font("multimedia/fonts/Turok.ttf", 25)
    
    def _load_characters(self):
        """Carrega personagens disponíveis"""
        characters = []
        
        for char_name, char_data in CHARACTERS.items():
            try:
                idle_anim = char_data["animations"].get("idle")
                if not idle_anim:
                    continue
                
                idle_path, idle_frames = idle_anim
                full_path = os.path.join("multimedia/images", char_data["path"], idle_path)
                idle_sheet = pygame.image.load(full_path).convert_alpha()
                
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
        
        return characters
    
    def handle_events(self, events):
        # Processar mensagens da rede
        while self.client.has_messages():
            msg = self.client.get_message()
            
            if msg.msg_type == MessageType.CHARACTER_SELECTED:
                # Oponente selecionou personagem
                opponent_char = msg.data.get("character")
                print(f"🎭 Oponente selecionou: {opponent_char}")
                self.opponent_character = opponent_char
            
            elif msg.msg_type == MessageType.BOTH_READY:
                # Ambos prontos, iniciar jogo!
                p1_char = msg.data.get("player1_character")
                p2_char = msg.data.get("player2_character")
                
                print(f"🎮 Ambos prontos! P1:{p1_char} vs P2:{p2_char}")
                
                return {
                    "next": "online_game",
                    "client": self.client,
                    "player_id": self.player_id,
                    "player1_character": p1_char,
                    "player2_character": p2_char,
                    "is_host": self.is_host
                }
        
        # Processar input do jogador
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
                        # Confirmar seleção
                        self.my_character = self.characters[self.selected_option]["name"]
                        self.ready = True
                        
                        # Enviar ao servidor
                        self.client.select_character(self.my_character)
                        print(f"✅ Selecionou: {self.my_character}")
                
                if event.key == pygame.K_ESCAPE:
                    # Voltar (desconectar)
                    self.client.disconnect()
                    return {"next": "menu"}
        
        return None
    
    def update(self):
        """Atualiza animação"""
        now = pygame.time.get_ticks()
        character = self.characters[self.selected_option]
        
        if now - self.anim_timer >= self.anim_speed:
            self.anim_index += 1
            if self.anim_index >= character["idle_frames"]:
                self.anim_index = 0
            self.anim_timer = now
    
    def draw(self, screen):
        """Desenha o character select"""
        screen.fill((20, 20, 20))
        
        # Title
        title = self.title_font.render("Select Your Fighter", True, (255, 0, 0))
        screen.blit(title, (self.screen_width // 2 - title.get_width() // 2, 50))
        
        # Player info
        player_text = f"You are Player {self.player_id}"
        player_label = self.message_font.render(player_text, True, (255, 255, 0))
        screen.blit(player_label, (20, 20))
        
        # Desenhar nomes de personagens
        total_chars = len(self.characters)
        spacing = min(200, self.screen_width // (total_chars + 1))
        
        for i, character in enumerate(self.characters):
            if self.ready and i == self.selected_option:
                color = (0, 255, 0)  # Verde se confirmou
            elif i == self.selected_option:
                color = (255, 255, 0)  # Amarelo se selecionado
            else:
                color = (150, 150, 150)  # Cinza se não selecionado
            
            txt = self.option_font.render(character["name"], True, color)
            x_pos = (self.screen_width // 2) - ((total_chars - 1) * spacing // 2) + (i * spacing)
            screen.blit(txt, (x_pos - txt.get_width() // 2, self.screen_height - 100))
        
        # Desenhar preview da personagem selecionada
        character = self.characters[self.selected_option]
        
        sheet = character["image"]
        size = character["size"]
        scale = character["scale"]
        offset_x, offset_y = character.get("offset", [0, 0])
        
        sheet_width = sheet.get_width()
        sheet_height = sheet.get_height()
        frame_count = character["idle_frames"]
        
        # Calcular largura do frame (não assumir quadrado!)
        frame_width = sheet_width // frame_count
        frame_height = sheet_height
        
        frame_x = self.anim_index * frame_width
        
        # Garantir que não excede os limites
        if frame_x + frame_width > sheet_width:
            self.anim_index = 0
            frame_x = 0
        
        # Extrair o frame atual
        frame = sheet.subsurface(frame_x, 0, frame_width, frame_height)
        
        # Escalar o frame
        preview_image = pygame.transform.scale(
            frame, (int(frame_width * scale), int(frame_height * scale)))
        
        # Centralizar na tela (com offset)
        preview_x = self.screen_width // 2 - preview_image.get_width() // 2 + offset_x
        preview_y = 300 - preview_image.get_height() // 2 + offset_y
        
        screen.blit(preview_image, (preview_x, preview_y))
        
        # Nome da personagem selecionada
        name_surface = self.title_font.render(character["name"], True, (255, 255, 0))
        name_rect = name_surface.get_rect(center=(self.screen_width // 2, 450))
        screen.blit(name_surface, name_rect)
        
        # Status
        if self.ready:
            if self.opponent_character:
                status = f"Waiting for game to start..."
                opponent_status = f"Opponent selected: {self.opponent_character}"
            else:
                status = f"Waiting for opponent to select..."
                opponent_status = ""
        else:
            status = "← → to select | ENTER to confirm"
            if self.opponent_character:
                opponent_status = f"Opponent selected: {self.opponent_character}"
            else:
                opponent_status = "Opponent is selecting..."
        
        status_label = self.message_font.render(status, True, (200, 200, 200))
        screen.blit(status_label, (self.screen_width // 2 - status_label.get_width() // 2, 510))
        
        if opponent_status:
            opp_label = self.message_font.render(opponent_status, True, (100, 200, 255))
            screen.blit(opp_label, (self.screen_width // 2 - opp_label.get_width() // 2, 540))
        
        # ESC para voltar
        esc_label = self.message_font.render("ESC to disconnect", True, (150, 150, 150))
        screen.blit(esc_label, (self.screen_width // 2 - esc_label.get_width() // 2, 
                                self.screen_height - 30))