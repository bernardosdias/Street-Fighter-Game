import pygame


class AnimatedBackground:
    def __init__(self, path, width, height):
        self.width = width
        self.height = height
        self.frames = []
        self.durations = []
        self.current_index = 0
        self.next_frame_at = 0

        if str(path).lower().endswith(".gif"):
            self._load_gif_frames(path)

        if not self.frames:
            self._load_static(path)

    def _load_static(self, path):
        image = pygame.image.load(path).convert_alpha()
        self.frames = [pygame.transform.scale(image, (self.width, self.height))]
        self.durations = [1000]
        self.current_index = 0
        self.next_frame_at = pygame.time.get_ticks() + self.durations[0]

    def _load_gif_frames(self, path):
        try:
            from PIL import Image, ImageSequence
        except Exception:
            return

        try:
            gif = Image.open(path)
            for frame in ImageSequence.Iterator(gif):
                rgba = frame.convert("RGBA")
                raw = rgba.tobytes()
                surf = pygame.image.fromstring(raw, rgba.size, "RGBA").convert_alpha()
                surf = pygame.transform.scale(surf, (self.width, self.height))
                self.frames.append(surf)

                duration = frame.info.get("duration", 100)
                if not isinstance(duration, int) or duration <= 0:
                    duration = 100
                self.durations.append(duration)
        except Exception:
            self.frames = []
            self.durations = []
            return

        if self.frames:
            self.current_index = 0
            self.next_frame_at = pygame.time.get_ticks() + self.durations[0]

    def update(self):
        if len(self.frames) <= 1:
            return

        now = pygame.time.get_ticks()
        if now >= self.next_frame_at:
            self.current_index = (self.current_index + 1) % len(self.frames)
            self.next_frame_at = now + self.durations[self.current_index]

    def draw(self, screen):
        if not self.frames:
            return
        screen.blit(self.frames[self.current_index], (0, 0))
