import pygame


class Fighter():
    def __init__(self, x, y, flip, data, sprite_sheet, animation_steps):
        self.size = data[0]
        self.image_scale = data[1]
        self.offset = data[2]
        self.flip = flip
        self.animation_list = self.load_images(sprite_sheet, animation_steps)
        self.action = 0  # 0:idel #!:run #3:attack1 #4: attack2 #5hit #6:death
        self.frame_index = 0
        self.image = self.animation_list[self.action][self.frame_index]
        self.update_time = pygame.time.get_ticks()
        self.rect = pygame.Rect((x, y,  80, 180))
        self.vel_y = 0
        self.jump = False
        self.attack_type = 0
        self.attacking = False
        self.health = 100

    def load_images(self, sprite_sheet, animation_steps):
        # EXTRACT IMAGES FROM SPRITESHEET
        animation_list = []
        for y, animation in enumerate(animation_steps):
            temp_img_list = []
            for x in range(animation):
                temp_img = sprite_sheet.subsurface(
                    x * self.size, y * self.size, self.size, self.size)
                temp_img_list.append(pygame.transform.scale(
                    temp_img, (self.size * self.image_scale, self.size * self.image_scale)))
            animation_list.append(temp_img_list)
        return animation_list

    def move(self, screen_width, screen_height, surface, target):
        SPEED = 10
        GRAVITY = 2
        dx = 0
        dy = 0

        # get keypresses
        key = pygame.key.get_pressed()

        # CAN ONLY PERFORM OTHER ACTIONS IF NOT ATTACKING
        if self.attacking == False:
            # movement
            if key[pygame.K_a]:
                dx = -SPEED
            if key[pygame.K_d]:
                dx = SPEED

            # vertical movement
            if key[pygame.K_w] and self.jump == False:
                self.vel_y = -30
                self.jump = True
            # ATTACK PRESSES
            if key[pygame.K_r] or key[pygame.K_t]:
                self.attack(surface, target)

                # determine attack type
                if key[pygame.K_r]:
                    self.attack_type = 1
                if key[pygame.K_t]:
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

        # UPDATE PLAYER POSITION
        self.rect.x += dx
        self.rect.y += dy

    # HANDLE ANIMATION UPDATES

    def update(self):
        animation_cd = 100  # milis
        # UPDATE IMAGE
        self.image = self.animation_list[self.action][self.frame_index]
        # CHECKS IF ENOUGH TIME HAS PASSED SINCE THE LAST UPDATE
        if pygame.time.get_ticks() - self.update_time > animation_cd:
            self.frame_index +=1
            self.update_time = pygame.time.get_ticks()
        # CHECK IF THE ANIMATION HAS FINISHED
        if self.frame_index >= len(self.animation_list[self.action]):
            self.frame_index = 0

    def attack(self, surface, target):
        self.attacking = True
        attacking_rect = pygame.Rect(self.rect.centerx - (
            2 * self.rect.width * self.flip), self.rect.y, 2 * self.rect.width, self.rect.height)
        if attacking_rect.colliderect(target.rect):
            target.health -= 10

        pygame.draw.rect(surface, (0, 255, 0), attacking_rect)

    def draw_fighter(self, surface):
        img = pygame.transform.flip(self.image, self.flip, False)
        #pygame.draw.rect(surface, (255, 0, 0), self.rect)
        surface.blit(
            img, (self.rect.x - (self.offset[0] * self.image_scale), self.rect.y - self.offset[1] * self.image_scale))
