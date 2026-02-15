from core.config import IMAGES_DIR
from core.assets import image_path


SUPPORTED_MAP_EXTENSIONS = {".png", ".jpg", ".jpeg", ".jfif", ".webp", ".bmp", ".gif"}


def _iter_map_files():
    map_dirs = [IMAGES_DIR / "maps", IMAGES_DIR / "background"]
    seen_paths = set()
    for map_dir in map_dirs:
        if not (map_dir.exists() and map_dir.is_dir()):
            continue
        for entry in sorted(map_dir.iterdir()):
            if not entry.is_file():
                continue
            if entry.suffix.lower() not in SUPPORTED_MAP_EXTENSIONS:
                continue
            if entry.name.lower() == "menu_background.jpg":
                continue
            normalized = str(entry.resolve()).lower()
            if normalized in seen_paths:
                continue
            seen_paths.add(normalized)
            yield entry


def discover_maps():
    maps = []
    for entry in _iter_map_files():
        maps.append(
            {
                "id": entry.stem,
                "name": entry.stem.replace("_", " ").title(),
                "path": str(entry),
            }
        )

    if not maps:
        maps.append(
            {
                "id": "default",
                "name": "Default Arena",
                "path": image_path("background", "background.jpg"),
            }
        )

    return maps
