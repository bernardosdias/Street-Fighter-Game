import pygame
import threading
from network.server import GameServer
from network.client import GameClient


class OnlineMenuFrame:
    """Menu para multiplayer online"""
    
    def __init__(self, screen_width, screen_height):
        self.screen_width = screen_width
        self.screen_height = screen_height
        
        self.options = ["Host Game (LAN)", "Join Game", "Back to Menu"]
        self.selected_option = 0
        
        # Estado
        self.state = "MENU"  # MENU, HOSTING, JOINING, INPUT_IP, WAITING
        self.message = ""
        self.error_message = ""
        
        # Network
        self.server = None
        self.client = None
        self.server_thread = None
        
        # Input de IP
        self.ip_input = "127.0.0.1"
        self.input_active = False
        
        # Fonts
        self.title_font = pygame.font.Font("multimedia/fonts/Turok.ttf", 60)
        self.option_font = pygame.font.Font("multimedia/fonts/Turok.ttf", 40)
        self.message_font = pygame.font.Font("multimedia/fonts/Turok.ttf", 25)
        
        # Background
        try:
            self.bg_image = pygame.image.load(
                "multimedia/images/background/menu_background.jpg").convert_alpha()
        except:
            self.bg_image = None
    
    def handle_events(self, events):
        for event in events:
            if event.type == pygame.KEYDOWN:
                
                # Estado de INPUT_IP (digitando IP)
                if self.state == "INPUT_IP":
                    if event.key == pygame.K_RETURN:
                        # Confirmar IP e conectar
                        self._join_game()
                    elif event.key == pygame.K_BACKSPACE:
                        self.ip_input = self.ip_input[:-1]
                    elif event.key == pygame.K_ESCAPE:
                        # Cancelar
                        self.state = "MENU"
                        self.ip_input = "127.0.0.1"
                    elif event.unicode.isprintable():
                        # Adicionar caractere
                        if len(self.ip_input) < 50:
                            self.ip_input += event.unicode
                
                # Estado MENU (selecionando opção)
                elif self.state == "MENU":
                    if event.key == pygame.K_UP:
                        self.selected_option = (self.selected_option - 1) % len(self.options)
                    elif event.key == pygame.K_DOWN:
                        self.selected_option = (self.selected_option + 1) % len(self.options)
                    elif event.key == pygame.K_RETURN:
                        if self.selected_option == 0:
                            # Host Game
                            self._host_game()
                        elif self.selected_option == 1:
                            # Join Game
                            self.state = "INPUT_IP"
                            self.ip_input = "127.0.0.1"
                        elif self.selected_option == 2:
                            # Back to Menu
                            return {"next": "menu"}
                    elif event.key == pygame.K_ESCAPE:
                        return {"next": "menu"}
                
                # Estado WAITING (aguardando outro jogador)
                elif self.state == "WAITING":
                    if event.key == pygame.K_ESCAPE:
                        # Cancelar e voltar
                        self._cleanup()
                        return {"next": "menu"}
        
        # Verificar se ambos jogadores conectaram (quando em HOSTING ou JOINING)
        if self.state in ["HOSTING", "JOINING", "WAITING"]:
            if self.client and self.client.has_messages():
                msg = self.client.get_message()
                
                if msg.type.value == "BOTH_READY":
                    # Ambos jogadores selecionaram personagens!
                    # Transitar para character select online
                    return {
                        "next": "online_character_select",
                        "client": self.client,
                        "player_id": self.client.player_id,
                        "is_host": (self.state == "HOSTING")
                    }
        
        return None
    
    def _host_game(self):
        """Inicia servidor e conecta como host"""
        self.state = "HOSTING"
        self.message = "Iniciando servidor..."
        self.error_message = ""
        
        try:
            # Iniciar servidor em thread separada
            self.server = GameServer()
            self.server_thread = threading.Thread(target=self.server.start, daemon=True)
            self.server_thread.start()
            
            # Aguardar um pouco para o servidor iniciar
            pygame.time.wait(500)
            
            # Conectar como cliente ao próprio servidor
            self.client = GameClient()
            if self.client.connect("127.0.0.1"):
                local_ip = self.server.get_local_ip()
                self.message = f"Servidor iniciado!"
                self.state = "WAITING"
                self.error_message = f"Partilha este IP: {local_ip}"
                print(f"✅ Hosting em {local_ip}:5555")
            else:
                self.error_message = "Erro ao conectar ao servidor local"
                self.state = "MENU"
                self._cleanup()
        
        except Exception as e:
            self.error_message = f"Erro ao iniciar servidor: {e}"
            self.state = "MENU"
            self._cleanup()
    
    def _join_game(self):
        """Conecta ao servidor como cliente"""
        self.state = "JOINING"
        self.message = f"Conectando a {self.ip_input}..."
        self.error_message = ""
        
        try:
            self.client = GameClient()
            if self.client.connect(self.ip_input):
                self.message = "Conectado com sucesso!"
                self.state = "WAITING"
                self.error_message = "Aguardando host iniciar o jogo..."
                print(f"✅ Conectado a {self.ip_input}")
            else:
                self.error_message = "Falha ao conectar. Verifica o IP!"
                self.state = "MENU"
        
        except Exception as e:
            self.error_message = f"Erro: {e}"
            self.state = "MENU"
    
    def _cleanup(self):
        """Limpa recursos de rede"""
        if self.client:
            self.client.disconnect()
            self.client = None
        
        if self.server:
            self.server.stop()
            self.server = None
    
    def update(self):
        """Atualiza o estado do menu"""
        pass
    
    def draw(self, screen):
        """Desenha o menu"""
        # Background
        if self.bg_image:
            bg = pygame.transform.scale(self.bg_image, (self.screen_width, self.screen_height))
            screen.blit(bg, (0, 0))
        else:
            screen.fill((20, 20, 20))
        
        # Title
        title = self.title_font.render("Online Multiplayer", True, (255, 0, 0))
        title_rect = title.get_rect(center=(self.screen_width // 2, 100))
        screen.blit(title, title_rect)
        
        # Desenhar baseado no estado
        if self.state == "MENU":
            self._draw_menu(screen)
        elif self.state == "INPUT_IP":
            self._draw_ip_input(screen)
        elif self.state in ["HOSTING", "JOINING", "WAITING"]:
            self._draw_waiting(screen)
    
    def _draw_menu(self, screen):
        """Desenha as opções do menu"""
        for i, option in enumerate(self.options):
            color = (255, 255, 0) if i == self.selected_option else (255, 255, 255)
            text = self.option_font.render(option, True, color)
            text_rect = text.get_rect(center=(self.screen_width // 2, 250 + i * 70))
            screen.blit(text, text_rect)
        
        # Instruções
        instructions = self.message_font.render(
            "↑↓ to select | ENTER to confirm | ESC to go back", 
            True, (150, 150, 150)
        )
        screen.blit(instructions, (self.screen_width // 2 - instructions.get_width() // 2, 
                                   self.screen_height - 50))
    
    def _draw_ip_input(self, screen):
        """Desenha a tela de input de IP"""
        # Prompt
        prompt = self.option_font.render("Enter Server IP:", True, (255, 255, 255))
        prompt_rect = prompt.get_rect(center=(self.screen_width // 2, 250))
        screen.blit(prompt, prompt_rect)
        
        # Input box
        input_box_rect = pygame.Rect(
            self.screen_width // 2 - 250, 320, 500, 50
        )
        pygame.draw.rect(screen, (255, 255, 255), input_box_rect, 2)
        
        # IP text
        ip_text = self.option_font.render(self.ip_input, True, (255, 255, 0))
        screen.blit(ip_text, (input_box_rect.x + 10, input_box_rect.y + 10))
        
        # Cursor piscando
        if pygame.time.get_ticks() % 1000 < 500:
            cursor_x = input_box_rect.x + 10 + ip_text.get_width() + 5
            pygame.draw.line(
                screen, (255, 255, 0),
                (cursor_x, input_box_rect.y + 10),
                (cursor_x, input_box_rect.y + 40),
                2
            )
        
        # Instruções
        instructions = [
            "ENTER to connect",
            "ESC to cancel"
        ]
        y = 420
        for instruction in instructions:
            text = self.message_font.render(instruction, True, (150, 150, 150))
            screen.blit(text, (self.screen_width // 2 - text.get_width() // 2, y))
            y += 30
    
    def _draw_waiting(self, screen):
        """Desenha a tela de espera"""
        # Mensagem principal
        msg = self.message_font.render(self.message, True, (255, 255, 255))
        msg_rect = msg.get_rect(center=(self.screen_width // 2, 250))
        screen.blit(msg, msg_rect)
        
        # Mensagem secundária (IP ou erro)
        if self.error_message:
            color = (255, 100, 100) if "Erro" in self.error_message else (100, 255, 100)
            error = self.message_font.render(self.error_message, True, color)
            error_rect = error.get_rect(center=(self.screen_width // 2, 300))
            screen.blit(error, error_rect)
        
        # Loading animation
        dots = "." * ((pygame.time.get_ticks() // 500) % 4)
        loading = self.option_font.render(f"Aguardando{dots}", True, (255, 255, 0))
        loading_rect = loading.get_rect(center=(self.screen_width // 2, 350))
        screen.blit(loading, loading_rect)
        
        # Instruções
        instructions = self.message_font.render(
            "ESC to cancel", True, (150, 150, 150)
        )
        screen.blit(instructions, (self.screen_width // 2 - instructions.get_width() // 2, 
                                   self.screen_height - 50))