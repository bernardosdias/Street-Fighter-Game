from pathlib import Path

# Project root: .../Street-Fighter-Game
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Display config
SCREEN_WIDTH = 1000
SCREEN_HEIGHT = 600
FPS = 60
WINDOW_TITLE = "Street Fighter - Online"

# Asset roots
MULTIMEDIA_DIR = PROJECT_ROOT / "multimedia"
FONTS_DIR = MULTIMEDIA_DIR / "fonts"
IMAGES_DIR = MULTIMEDIA_DIR / "images"
AUDIO_DIR = MULTIMEDIA_DIR / "audio"

# Shared font
DEFAULT_FONT_FILE = "Turok.ttf"

