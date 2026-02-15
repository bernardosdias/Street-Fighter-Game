from pathlib import Path


SSF2_DIR = Path("multimedia/images/Super Street Fighter II The New Challengers")
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".jfif", ".webp", ".bmp", ".gif"}
BASE_IMAGES_DIR = Path("multimedia/images").resolve()


def _safe_title(name):
    return " ".join(part.capitalize() for part in name.replace("_", " ").split())


def _estimate_frame_count(image_path):
    try:
        from PIL import Image

        with Image.open(image_path) as img:
            width, height = img.size
    except Exception:
        return 1

    if height <= 0:
        return 1

    ratio = width / float(height)
    if ratio < 1.35:
        return 1
    return max(1, min(24, int(round(ratio))))


def _estimate_scale(image_path):
    try:
        from PIL import Image

        with Image.open(image_path) as img:
            frame_height = img.size[1]
    except Exception:
        return 2

    if frame_height >= 240:
        return 1
    if frame_height >= 170:
        return 1.25
    if frame_height >= 130:
        return 1.5
    if frame_height >= 90:
        return 2
    return 2.5


def _iter_character_sheets():
    if not SSF2_DIR.exists() or not SSF2_DIR.is_dir():
        return []

    entries = []
    for char_dir in sorted(SSF2_DIR.iterdir()):
        if not char_dir.is_dir():
            continue

        sheets = sorted(
            [f for f in char_dir.iterdir() if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS]
        )
        if not sheets:
            continue

        entries.append((char_dir, sheets[0]))
    return entries


def _build_characters():
    characters = {}
    for char_dir, sheet in _iter_character_sheets():
        relative_dir = str(char_dir.resolve().relative_to(BASE_IMAGES_DIR)).replace("\\", "/")
        frame_count = _estimate_frame_count(sheet)
        scale = _estimate_scale(sheet)
        character_name = _safe_title(char_dir.name)

        characters[character_name] = {
            "path": relative_dir,
            "scale": scale,
            "size": 160,
            "offset": [0, 0],
            "foot_offset": 0,
            "attack_range": 2.5,
            "attack_sound": "sword.wav",
            "animations": {
                "idle": (sheet.name, frame_count),
                "run": (sheet.name, frame_count),
                "attack1": (sheet.name, frame_count),
                "attack2": (sheet.name, frame_count),
                "hit": (sheet.name, frame_count),
                "death": (sheet.name, frame_count),
            },
        }

    return characters


CHARACTERS = _build_characters()
