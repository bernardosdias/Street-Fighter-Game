import pygame
from fighters.fighter import Fighter
from pygame import mixer
from frames.menu import MenuFrame

mixer.init()
pygame.init()

# CREATE GAME WINDOW

SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600

# SET FRAME RATE
clock = pygame.time.Clock()
FPS = 60

# DEFINE COLORS
YELLOW = (255, 255, 0)
RED = (255, 0, 0)
WHITE = (255, 255, 255)

# DEFINE GAME VARIABLES
intro_count = 3
last_count_update = pygame.time.get_ticks()
score = [0, 0]  # PLAYER SCORES. [PI, P2]
round_over = False
ROUND_OVER_COOLDOWN = 2000
game_over = False

# DEFINE FIGHTER VARIABLES
WARRIOR_SIZE = 162
WARRIOR_SCALE = 4
WARRIOR_OFFSET = [72, 56]
WARRIOR_DATA = [WARRIOR_SIZE, WARRIOR_SCALE, WARRIOR_OFFSET]
WIZARD_SIZE = 250
WIZARD_SCALE = 3
WIZARD_OFFSET = [112, 107]
WIZARD_DATA = [WIZARD_SIZE, WIZARD_SCALE, WIZARD_OFFSET]

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Street Fighter")

# LOAD MUSIC AND SOUNDS
pygame.mixer.music.load("multimedia/audio/music.mp3")
pygame.mixer.music.set_volume(0.1)
pygame.mixer.music.play(-1, 0.0, 5000)
sword_sound = pygame.mixer.Sound("multimedia/audio/sword.wav")
sword_sound.set_volume(0.2)
staff_sound = pygame.mixer.Sound("multimedia/audio/staff.wav")
staff_sound.set_volume(0.2)

# LOAD WARRIOR AND WIZARD

warrior_sheet = pygame.image.load(
    "multimedia/images/warrior/warrior.png").convert_alpha()
wizard_sheet = pygame.image.load(
    "multimedia/images/wizard/wizard.png").convert_alpha()

# LOAD VICTORY IMAGE
victory_img = pygame.image.load(
    "multimedia/images/icons/victory.png").convert_alpha()

# DEFINE FONT
count_font = pygame.font.Font("multimedia/fonts/Turok.ttf", 80)
score_font = pygame.font.Font("multimedia/fonts/Turok.ttf", 30)

# FUNCTION FOR TEXT DRAW


def draw_text(text, font, text_col, x, y):
    img = font.render(text, True, text_col)
    screen.blit(img, (x, y))


# LOAD BACKGROUD IMAGE

bg_image = pygame.image.load(
    "multimedia/images/background/background.jpg").convert_alpha()

# DEFINE NUMBER OF STEPS IN EACH ANIMATION

WARRIOR_ANIMATION_STEPS = [10, 8, 1, 7, 7, 3, 7]
WIZARD_ANIMATION_STEPS = [8, 8, 1, 8, 8, 3, 7]

# DRAW BACKGROUND


def draw_bg():
    scaled_bg = pygame.transform.scale(bg_image, (SCREEN_WIDTH, SCREEN_HEIGHT))
    screen.blit(scaled_bg, (0, 0))

# DRAW GAME WINS


def draw_game_wins(screen, wins, x_start, y, radius=12, spacing=40):
    for i in range(3):
        x = x_start + i * spacing
        if i < wins:
            pygame.draw.circle(screen, YELLOW, (x, y), radius)
        else:
            pygame.draw.circle(screen, YELLOW, (x, y), radius, 2)


# DRAW HP


def draw_hp(health, x, y):
    ratio = health / 100
    pygame.draw.rect(screen, WHITE, (x - 2, y - 2, 404, 34))
    pygame.draw.rect(screen, RED, (x, y, 400, 30))
    pygame.draw.rect(screen, YELLOW, (x, y,  400*ratio, 30))

    # CREACT 2 INSTANCES OF FIGHTERS


figther_1 = Fighter(1, 200, 310, False, WARRIOR_DATA,
                    warrior_sheet, WARRIOR_ANIMATION_STEPS, sword_sound)
figther_2 = Fighter(2, 700, 310, True, WIZARD_DATA,
                    wizard_sheet, WIZARD_ANIMATION_STEPS, staff_sound)

#CREATE MENU FRAME
menu_frame = MenuFrame(SCREEN_WIDTH, SCREEN_HEIGHT)
current_frame = menu_frame

# GAME LOOP
run = True

while run:

    clock.tick(FPS)

    events = pygame.event.get()
    for event in events:
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()

    current_frame.handle_events(events)
    current_frame.update()
    current_frame.draw(screen)

    pygame.display.update()

    # clock.tick(FPS)

    # events = pygame.event.get()

    # for event in events:
    #     if event.type == pygame.QUIT:
    #         pygame.quit()
    #         exit()
    
    # next_frame = current_frame.handle_events(events)
    # if next_frame == "character_selection":
    #     #from character_selection import CharacterSelection
    #     #current_frame = CharacterSelection(SCREEN_WIDTH, SCREEN_HEIGHT)
    
    # current_frame.update()
    # current_frame.draw(screen)

    # # DRAW BACKGROUND
    # draw_bg()

    # # SHOW PLAYER HP AND SCORE
    # draw_hp(figther_1.health, 20, 20)
    # draw_hp(figther_2.health, 580, 20)
    # draw_game_wins(screen, score[0], 30, 80)
    # draw_game_wins(screen, score[1], 590, 80)

    # if intro_count <= 0:
    #     # MOVE FIGHTERS
    #     figther_1.move(SCREEN_WIDTH, SCREEN_HEIGHT,
    #                    screen, figther_2, round_over)
    #     figther_2.move(SCREEN_WIDTH, SCREEN_HEIGHT,
    #                    screen, figther_1, round_over)
    # else:
    #     # DISPLAY COUNT TIMER
    #     draw_text(str(intro_count), count_font, RED,
    #               SCREEN_WIDTH/2, SCREEN_HEIGHT / 3)
    #     if (pygame.time.get_ticks() - last_count_update) >= 1000:
    #         intro_count -= 1
    #         last_count_update = pygame.time.get_ticks()

    # # UPDATE FIGHTERS
    # figther_1.update()
    # figther_2.update()

    # # DRAW FIGHTERS
    # figther_1.draw_fighter(screen)
    # figther_2.draw_fighter(screen)

    # # CHECK FOR PLAYER DEFEATED
    # if round_over == False:
    #     if figther_1.alive == False:
    #         score[1] += 1
    #         round_over = True
    #         round_over_time = pygame.time.get_ticks()
    #         print(score)
    #     elif figther_2.alive == False:
    #         score[0] += 1
    #         round_over = True
    #         round_over_time = pygame.time.get_ticks()
    # else:
    #     # DISPLAY VICTORY IMAGE
    #     screen.blit(victory_img, (360, 150))
    #     if pygame.time.get_ticks() - round_over_time > ROUND_OVER_COOLDOWN:
    #         round_over = False
    #         intro_count = 3
    #         figther_1 = Fighter(1, 200, 310, False, WARRIOR_DATA,
    #                             warrior_sheet, WARRIOR_ANIMATION_STEPS, sword_sound)
    #         figther_2 = Fighter(2, 700, 310, True, WIZARD_DATA,
    #                             wizard_sheet, WIZARD_ANIMATION_STEPS, staff_sound)

    # # EVENT HANDLER
    # for event in pygame.event.get():
    #     if event.type == pygame.QUIT:
    #         run = False

    # # UPDATE DISPLAY
    # pygame.display.update()

# EXIT PYGAME
pygame.quit()
