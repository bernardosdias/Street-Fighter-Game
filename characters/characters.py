from pathlib import Path


SSF2_DIR = Path("multimedia/images/Super Street Fighter II The New Challengers")
SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".jfif", ".webp", ".bmp", ".gif"}
BASE_IMAGES_DIR = Path("multimedia/images").resolve()

# Relative atlas regions: (x, y, w, h)
REGIONS = {
    # Tightened slices to isolate common move rows across the SSF2 sheets.
    "idle": (0.00, 0.00, 0.12, 0.12),
    "run": (0.12, 0.00, 0.16, 0.12),
    "jump": (0.28, 0.00, 0.16, 0.12),
    "attack1": (0.00, 0.12, 0.34, 0.14),
    "attack2": (0.00, 0.26, 0.34, 0.14),
    "hit": (0.00, 0.72, 0.30, 0.10),
    "death": (0.78, 0.72, 0.22, 0.10),
    "portrait": (0.62, 0.86, 0.18, 0.12),
}

# Dedicated region for character-select idle thumbnails.
# Narrower height avoids leaking into next rows (e.g. "L.Punch" labels).
SELECT_IDLE_REGION = (0.00, 0.00, 0.12, 0.09)

# Per-character overrides for character-select idle thumbnails.
# Format: "Character Name": {"region": (x, y, w, h), "frames": <int or None>}
SELECT_IDLE_OVERRIDES = {
    # Keep empty unless a character needs explicit select-only crop overrides.
}

FRAME_COUNTS = {
    # Hints tuned for SSF2 atlas slices.
    "idle": 4,
    "run": 6,
    "jump": 4,
    "attack1": 6,
    "attack2": 6,
    "hit": 3,
    "death": 4,
}


def _safe_title(name):
    return " ".join(part.capitalize() for part in name.replace("_", " ").split())


def _estimate_scale(image_path):
    try:
        from PIL import Image

        with Image.open(image_path) as img:
            # Base scale on idle region frame height, not full atlas height.
            frame_height = int(img.size[1] * REGIONS["idle"][3])
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
        sheets = sorted([f for f in char_dir.iterdir() if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS])
        if not sheets:
            continue
        # Prefer atlas-like source sheets first (jpg/gif), then fallback to first file.
        preferred = [f for f in sheets if f.suffix.lower() in {".jpg", ".jpeg", ".gif", ".jfif", ".webp", ".bmp"}]
        entries.append((char_dir, preferred[0] if preferred else sheets[0]))
    return entries


def _anim_spec(sheet_name, state):
    return {
        "sheet": sheet_name,
        "region": REGIONS[state],
        "frames": FRAME_COUNTS[state],
    }


def _move_spec(filename, frames=None):
    return {
        "sheet": filename,
        "region": None,
        "frames": frames,
    }


def _slug_move_name(filename):
    stem = Path(filename).stem.strip().lower()
    stem = stem.replace(".", "").replace("-", " ").replace("/", " ")
    stem = " ".join(stem.split())
    return stem.replace(" ", "_")


def _build_move_specs_from_dir(char_dir):
    moves = {}
    for file in sorted(char_dir.iterdir()):
        if not file.is_file():
            continue
        if file.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue
        # Ignore atlas/source sheets; keep cropped move files.
        if file.name.lower() in {"balrog.jpg", "blanka.jpg", "cammy.jpg", "chun-li.jpg", "dee jay.jpg", "dhalsim.jpg", "e.honda.jpg", "fei long.jpg", "guile.jpg", "ken.jpg", "m. bison.gif", "ryu.gif", "sagat.jpg", "t. hawk.jpg", "vega.jpg", "zangief.jpg"}:
            continue

        key = _slug_move_name(file.name)
        moves[key] = {
            "sheet": file.name,
            "region": None,
            "frames": None,
            "move_name": Path(file.name).stem,
        }
    return moves


def _build_characters():
    characters = {}
    for char_dir, sheet in _iter_character_sheets():
        relative_dir = str(char_dir.resolve().relative_to(BASE_IMAGES_DIR)).replace("\\", "/")
        character_name = _safe_title(char_dir.name)
        scale = _estimate_scale(sheet)
        select_override = SELECT_IDLE_OVERRIDES.get(character_name, {})
        select_region = select_override.get("region", SELECT_IDLE_REGION)
        select_frames = select_override.get("frames", None)

        if character_name == "Balrog":
            balrog_moves = _build_move_specs_from_dir(char_dir)
            characters[character_name] = {
                "path": relative_dir,
                "scale": scale,
                "size": 160,
                "offset": [0, 0],
                "foot_offset": 0,
                "attack_range": 2.5,
                "attack_sound": "sword.wav",
                "select_idle_region": None,
                "select_idle_frames": None,
                "moves": balrog_moves,
                "action_moves": {
                    "idle": "idle",
                    "run": "walking",
                    "jump": "jumping",
                    "crouch": "crouch",
                    "attack1": "l_punch",
                    "attack2": "h_punch",
                    "special1": "dashing_punch",
                    "special2": "dashing_uppercut",
                    "hit": "hit",
                    "death": "ko",
                },
                "animations": {
                    "idle": _move_spec("Idle.png", None),
                    "run": _move_spec("Walking.png", None),
                    "jump": _move_spec("Jumping.png", None),
                    "attack1": _move_spec("L. Punch.png", None),
                    "attack2": _move_spec("H. Punch.png", None),
                    "hit": _move_spec("Hit.png", None),
                    "death": _move_spec("K.O .png", None),
                },
            }
            continue

        characters[character_name] = {
            "path": relative_dir,
            "scale": scale,
            "size": 160,
            "offset": [0, 0],
            "foot_offset": 0,
            "attack_range": 2.5,
            "attack_sound": "sword.wav",
            "select_portrait": {
                "sheet": sheet.name,
                "region": REGIONS["portrait"],
            },
            "select_idle_region": select_region,
            "select_idle_frames": select_frames,
            "animations": {
                "idle": _anim_spec(sheet.name, "idle"),
                "run": _anim_spec(sheet.name, "run"),
                "jump": _anim_spec(sheet.name, "jump"),
                "attack1": _anim_spec(sheet.name, "attack1"),
                "attack2": _anim_spec(sheet.name, "attack2"),
                "hit": _anim_spec(sheet.name, "hit"),
                "death": _anim_spec(sheet.name, "death"),
            },
        }

    return characters


CHARACTERS = _build_characters()
