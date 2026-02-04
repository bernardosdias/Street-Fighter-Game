import pygame
from characters.characters import CHARACTERS
from fighters.animation_loader import load_animation


class Fighter():
    def __init__(self, player, x, y, flip, character_name, sound):
        """
        Inicializa um Fighter usando o novo sistema de personagens.
        
        Args:
            player (int): Número do jogador (1 ou 2)
            x (int): Posição X inicial
            y (int): Posição Y inicial
            flip (bool): Se a personagem deve ser virada horizontalmente
            character_name (str): Nome da personagem do dicionário CHARACTERS
            sound (pygame.mixer.Sound): Som de ataque
        """
        self.player = player
        self.flip = flip
        self.attack_sound = sound
        
        # Carregar dados da personagem
        if character_name not in CHARACTERS:
            raise ValueError(f"Personagem '{character_name}' não encontrada em CHARACTERS")
        
        self.character_data = CHARACTERS[character_name]
        self.character_name = character_name
        self.scale = self.character_data["scale"]
        
        # Carregar animações
        self.animation_list = self.load_character_animations()
        
        # Estado da animação
        self.action = 0  # 0:idle #1:run #2:jump #3:attack1 #4:attack2 #5:hit #6:death
        self.frame_index = 0
        self.image = self.animation_list[self.action][self.frame_index]
        self.update_time = pygame.time.get_ticks()
        
        # Propriedades físicas
        self.rect = pygame.Rect((x, y, 80, 180))
        self.vel_y = 0
        self.running = False
        self.jump = False
        
        # Propriedades de combate
        self.attack_type = 0
        self.attacking = False
        self.attack_cd = 0
        self.hit = False
        self.health = 100
        self.alive = True
        
        # Offset para desenhar (ajustar conforme necessário)
        self.offset = (50, 50)

    def load_character_animations(self):
        """
        Carrega todas as animações da personagem usando o novo sistema.
        Retorna uma lista de listas de frames compatível com o sistema antigo.
        """
        animations = self.character_data["animations"]
        animation_list = []
        
        # Mapeamento de ações para nomes de animações
        # Índice: [idle, run, jump, attack1, attack2, hit, death]
        action_map = {
            0: "idle",
            1: "run", 
            2: "jump",      # Pode não existir em todas as personagens
            3: "attack1",   # ou "attack" se não houver attack1
            4: "attack2",   # Pode não existir
            5: "hit",
            6: "death"
        }
        
        for action_index in range(7):
            action_name = action_map[action_index]
            
            # Tentar encontrar a animação apropriada
            if action_name in animations:
                anim_path, frame_count = animations[action_name]
                frames = self.load_animation_from_spritesheet(anim_path, frame_count)
                animation_list.append(frames)
            elif action_name == "attack1" and "attack" in animations:
                # Fallback: se não há attack1, usa attack
                anim_path, frame_count = animations["attack"]
                frames = self.load_animation_from_spritesheet(anim_path, frame_count)
                animation_list.append(frames)
            elif action_name == "attack2" and "attack1" in animations:
                # Fallback: se não há attack2, usa attack1
                anim_path, frame_count = animations["attack1"]
                frames = self.load_animation_from_spritesheet(anim_path, frame_count)
                animation_list.append(frames)
            elif action_name == "attack2" and "attack" in animations:
                # Fallback: se não há attack2 nem attack1, usa attack
                anim_path, frame_count = animations["attack"]
                frames = self.load_animation_from_spritesheet(anim_path, frame_count)
                animation_list.append(frames)
            elif action_name == "jump":
                # Se não há jump, usa idle como fallback
                anim_path, frame_count = animations["idle"]
                frames = self.load_animation_from_spritesheet(anim_path, frame_count)
                animation_list.append(frames)
            else:
                # Fallback genérico: usar idle
                anim_path, frame_count = animations["idle"]
                frames = self.load_animation_from_spritesheet(anim_path, frame_count)
                animation_list.append(frames)
        
        return animation_list

    def load_animation_from_spritesheet(self, anim_path, frame_count):
        """
        Carrega uma animação usando a função load_animation do animation_loader.
        
        Args:
            anim_path (str): Caminho completo para o ficheiro de spritesheet
            frame_count (int): Número de frames na animação (não usado aqui, 
                              load_animation calcula automaticamente)
            
        Returns:
            list: Lista de superfícies pygame (frames)
        """
        import os
        
        try:
            # Separar o path e o filename
            directory = os.path.dirname(anim_path)
            filename = os.path.basename(anim_path)
            
            # Usar a função load_animation que já existe!
            frames = load_animation(directory, filename, self.scale)
            return frames
            
        except Exception as e:
            print(f"Erro ao carregar {anim_path}: {e}")
            # Retorna uma superfície em branco como fallback
            fallback = pygame.Surface((100, 100))
            fallback.fill((255, 0, 255))  # Magenta para indicar erro
            return [fallback]

    def move(self, screen_width, screen_height, surface, target, round_over):
        SPEED = 10
        GRAVITY = 2
        dx = 0
        dy = 0
        self.running = False
        self.attack_type = 0

        # get keypresses
        key = pygame.key.get_pressed()

        # CAN ONLY PERFORM OTHER ACTIONS IF NOT ATTACKING
        if self.attacking == False and self.alive == True and round_over == False:
            # CHECK PLAYER 1 CONTROLS
            if self.player == 1:
                # movement
                if key[pygame.K_a]:
                    dx = -SPEED
                    self.running = True
                if key[pygame.K_d]:
                    dx = SPEED
                    self.running = True

                # vertical movement
                if key[pygame.K_w] and self.jump == False:
                    self.vel_y = -30
                    self.jump = True
                # ATTACK PRESSES
                if key[pygame.K_r] or key[pygame.K_t]:
                    self.attack(target)

                    # determine attack type
                    if key[pygame.K_r]:
                        self.attack_type = 1
                    if key[pygame.K_t]:
                        self.attack_type = 2
            # CHECK PLAYER 2 CONTROLS
            if self.player == 2:
                # movement
                if key[pygame.K_LEFT]:
                    dx = -SPEED
                    self.running = True
                if key[pygame.K_RIGHT]:
                    dx = SPEED
                    self.running = True

                # vertical movement
                if key[pygame.K_UP] and self.jump == False:
                    self.vel_y = -30
                    self.jump = True
                # ATTACK PRESSES
                if key[pygame.K_KP1] or key[pygame.K_KP2]:
                    self.attack(target)

                    # determine attack type
                    if key[pygame.K_KP1]:
                        self.attack_type = 1
                    if key[pygame.K_KP2]:
                        self.attack_type = 2
        # APPLY GRAVITY
        self.vel_y += GRAVITY

        dy += self.vel_y

        # HANDLE COLISION WITH BORDERS
        if self.rect.left + dx < 0:
            dx = -self.rect.left
        if self.rect.right + dx > screen_width:
            dx = screen_width - self.rect.right
        if self.rect.bottom + dy > screen_height - 110:
            self.vel_y = 0
            dy = screen_height - 110 - self.rect.bottom
            self.jump = False

        # ENSURE PLAYERS FACE EACH OTHER
        if target.rect.centerx > self.rect.centerx:
            self.flip = False
        else:
            self.flip = True

        # APPLY ATTACK CD
        if self.attack_cd > 0:
            self.attack_cd -= 1

        # UPDATE PLAYER POSITION
        self.rect.x += dx
        self.rect.y += dy

    def update(self):
        """Atualiza a animação e estado do fighter"""
        
        # CHECK WHAT ACTION THE PLAYER IS DOING
        if self.health <= 0:
            self.health = 0
            self.alive = False
            self.update_action(6)  # 6 death
        elif self.hit == True:
            self.update_action(5)  # 5 Hit
        elif self.attacking == True:
            if self.attack_type == 1:
                self.update_action(3)  # 3 Attack 1
            elif self.attack_type == 2:
                self.update_action(4)  # 4 Attack 2
        elif self.jump == True:
            self.update_action(2)  # 2 Jump
        elif self.running == True:
            self.update_action(1)  # 1 Running
        else:
            self.update_action(0)  # 0 idle

        animation_cd = 50  # milis
        # UPDATE IMAGE
        self.image = self.animation_list[self.action][self.frame_index]
        # CHECKS IF ENOUGH TIME HAS PASSED SINCE THE LAST UPDATE
        if pygame.time.get_ticks() - self.update_time > animation_cd:
            self.frame_index += 1
            self.update_time = pygame.time.get_ticks()
        # CHECK IF THE ANIMATION HAS FINISHED
        if self.frame_index >= len(self.animation_list[self.action]):
            # IF THE PLAYER IS DEAD END THE ANIMATION
            if self.alive == False:
                self.frame_index = len(self.animation_list[self.action]) - 1
            else:
                self.frame_index = 0
                # CHECK IF AN ATTACK WAS EXECUTED
                if self.action == 3 or self.action == 4:
                    self.attacking = False
                    self.attack_cd = 20
                # CHECK IF DAMAGE WAS TAKEN
                if self.action == 5:
                    self.hit = False
                    # IF THE PLAYER WAS IN THE MIDDLE OF AN ATTACK, THEN THE ATTACK IS STOPPED
                    self.attacking = False
                    self.attack_cd = 20

    def attack(self, target):
        if self.attack_cd == 0:
            # EXECUTE ATTACK
            self.attacking = True
            self.attack_sound.play()
            attacking_rect = pygame.Rect(
                self.rect.centerx - (2 * self.rect.width * self.flip), 
                self.rect.y, 
                2 * self.rect.width, 
                self.rect.height
            )
            if attacking_rect.colliderect(target.rect):
                target.health -= 10
                target.hit = True

    def update_action(self, new_action):
        """Atualiza a ação atual do fighter"""
        # CHECK IF NEW ACTION IS DIFFERENT THAN PREV ONE
        if new_action != self.action:
            self.action = new_action
            # UPDATE ANIMATION SETTINGS
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def draw_fighter(self, surface):
        """Desenha o fighter na superfície"""
        img = pygame.transform.flip(self.image, self.flip, False)
        # Calcular offset baseado no tamanho da imagem
        draw_x = self.rect.x - (self.offset[0])
        draw_y = self.rect.y - (self.offset[1])
        surface.blit(img, (draw_x, draw_y))