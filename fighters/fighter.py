import pygame

from characters.characters import CHARACTERS
from fighters.animation_loader import load_animation, load_animation_region


class Fighter:
    def __init__(self, player, x, y, flip, character_name, sound):
        self.player = player
        self.flip = flip
        self.attack_sound = sound

        if character_name not in CHARACTERS:
            raise ValueError(f"Character '{character_name}' not found")

        self.character_data = CHARACTERS[character_name]
        self.character_name = character_name
        self.scale = self.character_data["scale"]
        self.size = self.character_data["size"]

        self.animation_list = self.load_character_animations()

        self.action = 0  # 0 idle, 1 run, 2 jump, 3 attack1, 4 attack2, 5 hit, 6 death
        self.frame_index = 0
        self.image = self.animation_list[self.action][self.frame_index]
        self.update_time = pygame.time.get_ticks()

        self.foot_offset = self.character_data.get("foot_offset", 0)
        self.offset = self.character_data.get("offset", [0, 0])

        hitbox_width = 80
        hitbox_height = 180
        self.rect = pygame.Rect(0, 0, hitbox_width, hitbox_height)
        self.rect.midbottom = (x, y)

        self.vel_y = 0
        self.running = False
        self.jump = False
        self.defending = False

        self.attack_type = 0
        self.attacking = False
        self.attack_cd = 0
        self.hit = False
        self.health = 100
        self.alive = True

    def load_character_animations(self):
        animations = self.character_data["animations"]
        animation_list = []

        action_map = {
            0: "idle",
            1: "run",
            2: "jump",
            3: "attack1",
            4: "attack2",
            5: "hit",
            6: "death",
        }

        for action_index in range(7):
            action_name = action_map[action_index]

            if action_name in animations:
                spec = animations[action_name]
            elif action_name == "attack1" and "attack" in animations:
                spec = animations["attack"]
            elif action_name == "attack2" and "attack1" in animations:
                spec = animations["attack1"]
            elif action_name == "attack2" and "attack" in animations:
                spec = animations["attack"]
            else:
                spec = animations["idle"]

            anim_filename, frame_count, region = self._parse_animation_spec(spec)
            frames = self.load_animation_from_spritesheet(
                anim_filename, frame_count, region
            )
            animation_list.append(frames)

        return animation_list

    def _parse_animation_spec(self, spec):
        if isinstance(spec, dict):
            filename = spec.get("sheet") or spec.get("file")
            frame_count = spec.get("frames")
            region = spec.get("region")
            if not filename:
                raise ValueError("Animation spec missing sheet/file")
            return filename, frame_count, region

        if isinstance(spec, (tuple, list)) and len(spec) >= 2:
            return spec[0], spec[1], None

        raise ValueError(f"Invalid animation spec: {spec}")

    def load_animation_from_spritesheet(self, anim_filename, frame_count, region=None):
        try:
            directory = self.character_data["path"]
            if region is not None:
                return load_animation_region(
                    directory, anim_filename, self.scale, region, frame_count
                )
            return load_animation(directory, anim_filename, self.scale, frame_count)
        except Exception as e:
            print(f"Error loading {anim_filename}: {e}")
            fallback = pygame.Surface((100, 100))
            fallback.fill((255, 0, 255))
            return [fallback]

    def move(self, screen_width, screen_height, surface, target, round_over, apply_damage=True, controls=None):
        speed = 10
        gravity = 2
        dx = 0
        dy = 0
        moving_left_input = False
        moving_right_input = False
        self.running = False
        self.defending = False
        self.attack_type = 0

        key = pygame.key.get_pressed()

        if not self.attacking and self.alive and not round_over:
            if controls is not None:
                if controls.get("left"):
                    moving_left_input = True
                    dx = -speed
                    self.running = True
                if controls.get("right"):
                    moving_right_input = True
                    dx = speed
                    self.running = True
                if controls.get("jump") and not self.jump:
                    self.vel_y = -30
                    self.jump = True
                if controls.get("attack1") or controls.get("attack2"):
                    self.attack(target, apply_damage=apply_damage)
                    if controls.get("attack1"):
                        self.attack_type = 1
                    if controls.get("attack2"):
                        self.attack_type = 2
            else:
                if self.player == 1:
                    if key[pygame.K_a]:
                        moving_left_input = True
                        dx = -speed
                        self.running = True
                    if key[pygame.K_d]:
                        moving_right_input = True
                        dx = speed
                        self.running = True
                    if key[pygame.K_w] and not self.jump:
                        self.vel_y = -30
                        self.jump = True
                    if key[pygame.K_r] or key[pygame.K_t]:
                        self.attack(target, apply_damage=apply_damage)
                        if key[pygame.K_r]:
                            self.attack_type = 1
                        if key[pygame.K_t]:
                            self.attack_type = 2
                if self.player == 2:
                    if key[pygame.K_LEFT]:
                        moving_left_input = True
                        dx = -speed
                        self.running = True
                    if key[pygame.K_RIGHT]:
                        moving_right_input = True
                        dx = speed
                        self.running = True
                    if key[pygame.K_UP] and not self.jump:
                        self.vel_y = -30
                        self.jump = True
                    if key[pygame.K_KP1] or key[pygame.K_KP2]:
                        self.attack(target, apply_damage=apply_damage)
                        if key[pygame.K_KP1]:
                            self.attack_type = 1
                        if key[pygame.K_KP2]:
                            self.attack_type = 2

        self.vel_y += gravity
        dy += self.vel_y

        if self.rect.left + dx < 0:
            dx = -self.rect.left
        if self.rect.right + dx > screen_width:
            dx = screen_width - self.rect.right
        if self.rect.bottom + dy > screen_height - 110:
            self.vel_y = 0
            dy = screen_height - 110 - self.rect.bottom
            self.jump = False

        self.flip = target.rect.centerx <= self.rect.centerx

        back_input = (self.flip and moving_right_input) or (
            (not self.flip) and moving_left_input
        )
        self.defending = back_input and self.alive and (not round_over)

        if self.attack_cd > 0:
            self.attack_cd -= 1

        self.rect.x += dx
        self.rect.y += dy

    def update(self):
        if self.health <= 0:
            self.health = 0
            self.alive = False
            self.update_action(6)
        elif self.hit:
            self.update_action(5)
        elif self.attacking:
            if self.attack_type == 1:
                self.update_action(3)
            elif self.attack_type == 2:
                self.update_action(4)
        elif self.jump:
            self.update_action(2)
        elif self.running:
            self.update_action(1)
        else:
            self.update_action(0)

        animation_cd = 50
        self.image = self.animation_list[self.action][self.frame_index]
        if pygame.time.get_ticks() - self.update_time > animation_cd:
            self.frame_index += 1
            self.update_time = pygame.time.get_ticks()

        if self.frame_index >= len(self.animation_list[self.action]):
            if not self.alive:
                self.frame_index = len(self.animation_list[self.action]) - 1
            else:
                self.frame_index = 0
                if self.action == 3 or self.action == 4:
                    self.attacking = False
                    self.attack_cd = 20
                if self.action == 5:
                    self.hit = False
                    self.attacking = False
                    self.attack_cd = 20

    def attack(self, target, apply_damage=True):
        if self.attack_cd == 0:
            self.attacking = True
            self.attack_sound.play()

            attack_range = self.character_data.get("attack_range", 2.0)
            attacking_rect = pygame.Rect(
                self.rect.centerx - (attack_range * self.rect.width * self.flip),
                self.rect.y,
                attack_range * self.rect.width,
                self.rect.height,
            )
            if apply_damage and attacking_rect.colliderect(target.rect):
                if target.defending:
                    return
                target.health -= 10
                target.hit = True

    def update_action(self, new_action):
        if new_action != self.action:
            self.action = new_action
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()

    def draw_fighter(self, surface):
        img = pygame.transform.flip(self.image, self.flip, False)
        foot_offset_scaled = self.foot_offset * self.scale
        draw_y = self.rect.bottom - img.get_height() + foot_offset_scaled
        draw_x = self.rect.centerx - (img.get_width() // 2)
        draw_x += self.offset[0]
        draw_y += self.offset[1]
        surface.blit(img, (draw_x, draw_y))
