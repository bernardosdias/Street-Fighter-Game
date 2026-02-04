import pygame
import os

def load_animation(path, filename, scale):
    image = pygame.image.load(os.path.join(path, filename)).convert_alpha()

    frame_height = image.get_height()
    frame_count = image.get_width()

    frames = []
    for i in range(frame_count):
        frame = image.subsurface(i * frame_height, 0, frame_height, frame_height)
        scaled_frame = pygame.transform.scale(
            frame, (int(frame_height * scale), int(frame_height * scale)))
        frames.append(scaled_frame)
    return frames