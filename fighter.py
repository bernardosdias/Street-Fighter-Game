import pygame


class Fighter():
    def __init__(self, x, y):
        self.rect = pygame.Rect((x, y,  80, 180))
        self.vel_y = 0
        self.jump = False
        self.attack_type = 0
        self.attacking = False
        self.health = 100

    def move(self, screen_width, screen_height, surface, target):
        SPEED = 10
        GRAVITY = 2
        dx = 0
        dy = 0

        # get keypresses
        key = pygame.key.get_pressed()

        #CAN ONLY PERFORM OTHER ACTIONS IF NOT ATTACKING
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

        # UPDATE PLAYER POSITION
        self.rect.x += dx
        self.rect.y += dy

    def attack(self, surface,target):
        self.attacking = True
        attacking_rect = pygame.Rect(self.rect.centerx, self.rect.y, 2 * self.rect.width, self.rect.height)
        if attacking_rect.colliderect(target.rect):
            target.health -= 10

        pygame.draw.rect(surface, (0, 255, 0), attacking_rect)

    def draw_fighter(self, surface):
        pygame.draw.rect(surface, (255, 0, 0), self.rect)
