import pygame
import os


def load_animation(path, filename, scale):
    full_path = os.path.join("multimedia/images", path, filename)
    sheet = pygame.image.load(full_path).convert_alpha()

    sheet_width = sheet.get_width()
    sheet_height = sheet.get_height()

    frame_height = sheet_height
    frame_width = frame_height

    if sheet_width % frame_height != 0:
        frame_width = sheet_width // max(1, sheet_width // frame_height)

    frame_count = sheet_width // frame_width

    frames = []

    for i in range(frame_count):
        x = i * frame_width

        if x + frame_width > sheet_width:
            break

        frame = sheet.subsurface(x, 0, frame_width, frame_height)

        if scale != 1:
            frame = pygame.transform.scale(
                frame,
                (int(frame_width * scale), int(frame_height * scale))
            )

        frames.append(frame)

    if not frames:
        fallback  = pygame.Surface((100, 100))
        fallback.fill((255, 0, 255))  # Magenta to indicate error
        frames.append(fallback)
    
    return frames