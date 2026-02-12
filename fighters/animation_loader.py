import pygame
from core.assets import image_path


def load_animation(path, filename, scale, frame_count=None):
    full_path = image_path(path, filename)
    sheet = pygame.image.load(full_path).convert_alpha()

    sheet_width = sheet.get_width()
    sheet_height = sheet.get_height()

    frame_height = sheet_height
    if frame_count is None or frame_count <= 0:
        frame_count = max(1, sheet_width // max(1, frame_height))
    frame_width = max(1, sheet_width // frame_count)

    frames = []

    for i in range(frame_count):
        x = i * frame_width

        if x >= sheet_width:
            break

        crop_width = min(frame_width, sheet_width - x)
        frame = sheet.subsurface(x, 0, crop_width, frame_height)

        if scale != 1:
            frame = pygame.transform.scale(
                frame,
                (int(crop_width * scale), int(frame_height * scale))
            )

        frames.append(frame)

    if not frames:
        fallback = pygame.Surface((100, 100))
        fallback.fill((255, 0, 255))  # Magenta to indicate error
        frames.append(fallback)

    return frames
