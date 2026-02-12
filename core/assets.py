from core.config import AUDIO_DIR, FONTS_DIR, IMAGES_DIR, DEFAULT_FONT_FILE


def font_path(filename=DEFAULT_FONT_FILE):
    return str(FONTS_DIR / filename)


def image_path(*parts):
    return str(IMAGES_DIR.joinpath(*parts))


def audio_path(filename):
    return str(AUDIO_DIR / filename)

