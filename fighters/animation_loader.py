import pygame
from core.assets import image_path


def _parse_region(region, width, height):
    if not region or len(region) != 4:
        return pygame.Rect(0, 0, width, height)

    x, y, w, h = region
    if 0 <= x <= 1 and 0 <= y <= 1 and 0 <= w <= 1 and 0 <= h <= 1:
        rx = int(width * x)
        ry = int(height * y)
        rw = int(width * w)
        rh = int(height * h)
    else:
        rx, ry, rw, rh = int(x), int(y), int(w), int(h)

    rx = max(0, min(rx, width - 1))
    ry = max(0, min(ry, height - 1))
    rw = max(1, min(rw, width - rx))
    rh = max(1, min(rh, height - ry))
    return pygame.Rect(rx, ry, rw, rh)


def _split_strip(sheet, scale, frame_count=None):
    sheet_width = sheet.get_width()
    sheet_height = sheet.get_height()
    frame_height = sheet_height

    if frame_count is None or frame_count <= 0:
        auto_frames = _split_by_detected_columns(sheet, scale)
        if auto_frames:
            return auto_frames
        frame_count = max(1, min(16, round(sheet_width / max(1, frame_height))))

    frame_width = max(1, sheet_width // frame_count)
    frames = []

    for i in range(frame_count):
        x = i * frame_width
        if x >= sheet_width:
            break

        crop_width = min(frame_width, sheet_width - x)
        frame = sheet.subsurface(x, 0, crop_width, frame_height)
        frame = _trim_and_key_frame(frame)

        if scale != 1:
            frame = pygame.transform.scale(
                frame,
                (int(frame.get_width() * scale), int(frame.get_height() * scale)),
            )

        frames.append(frame)

    if not frames:
        fallback = pygame.Surface((100, 100))
        fallback.fill((255, 0, 255))
        frames.append(fallback)

    return frames


def _split_by_detected_columns(sheet, scale):
    try:
        from PIL import Image
    except Exception:
        return None

    width, height = sheet.get_width(), sheet.get_height()
    if width < 8 or height < 8:
        return None

    try:
        raw = pygame.image.tostring(sheet, "RGB")
        pil_img = Image.frombytes("RGB", (width, height), raw)
        pix = pil_img.load()
    except Exception:
        return None

    c0 = pix[0, 0]
    c1 = pix[width - 1, 0]
    c2 = pix[0, height - 1]
    c3 = pix[width - 1, height - 1]
    bg = (
        (c0[0] + c1[0] + c2[0] + c3[0]) // 4,
        (c0[1] + c1[1] + c2[1] + c3[1]) // 4,
        (c0[2] + c1[2] + c2[2] + c3[2]) // 4,
    )

    # 1) Prefer atlas separator lines (vertical bright guide lines).
    separator_cols = [False] * width
    for x in range(width):
        bright = 0
        for y in range(height):
            r, g, b = pix[x, y]
            if r >= 185 and g >= 185 and b >= 185 and abs(r - g) < 24 and abs(g - b) < 24:
                bright += 1
        if bright / float(height) >= 0.55:
            separator_cols[x] = True

    sep_groups = []
    s = None
    for x, is_sep in enumerate(separator_cols):
        if is_sep and s is None:
            s = x
        elif not is_sep and s is not None:
            sep_groups.append((s, x - 1))
            s = None
    if s is not None:
        sep_groups.append((s, width - 1))

    if len(sep_groups) >= 2:
        boundaries = [0]
        for a, b in sep_groups:
            boundaries.append((a + b) // 2)
        boundaries.append(width - 1)
        boundaries = sorted(set(boundaries))

        frames = []
        for i in range(len(boundaries) - 1):
            x0 = boundaries[i] + 1
            x1 = boundaries[i + 1] - 1
            if x1 <= x0:
                continue
            if (x1 - x0 + 1) < max(4, width // 120):
                continue
            crop = sheet.subsurface(pygame.Rect(x0, 0, x1 - x0 + 1, height))
            crop = _trim_and_key_frame(crop)
            if scale != 1:
                crop = pygame.transform.scale(
                    crop,
                    (int(crop.get_width() * scale), int(crop.get_height() * scale)),
                )
            frames.append(crop)

        if len(frames) >= 2:
            return frames[:24]

    # 2) Fallback: detect foreground column groups.
    y_start = int(height * 0.18)
    col_has_sprite = [False] * width
    for x in range(width):
        for y in range(y_start, height):
            r, g, b = pix[x, y]
            diff = abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2])
            if diff > 48:
                col_has_sprite[x] = True
                break

    groups = []
    start = None
    for x, used in enumerate(col_has_sprite):
        if used and start is None:
            start = x
        elif not used and start is not None:
            groups.append((start, x - 1))
            start = None
    if start is not None:
        groups.append((start, width - 1))

    min_group_w = max(3, width // 180)
    groups = [(a, b) for (a, b) in groups if (b - a + 1) >= min_group_w]
    if len(groups) < 2:
        return None

    frames = []
    for a, b in groups[:24]:
        pad = 1
        x0 = max(0, a - pad)
        x1 = min(width - 1, b + pad)
        crop = sheet.subsurface(pygame.Rect(x0, 0, x1 - x0 + 1, height))
        crop = _trim_and_key_frame(crop)
        if scale != 1:
            crop = pygame.transform.scale(
                crop,
                (int(crop.get_width() * scale), int(crop.get_height() * scale)),
            )
        frames.append(crop)

    return frames or None


def load_animation(path, filename, scale, frame_count=None):
    full_path = image_path(path, filename)
    sheet = pygame.image.load(full_path).convert_alpha()
    return _split_strip(sheet, scale, frame_count)


def load_animation_region(path, filename, scale, region, frame_count=None):
    full_path = image_path(path, filename)
    sheet = pygame.image.load(full_path).convert_alpha()
    rect = _parse_region(region, sheet.get_width(), sheet.get_height())
    cropped = sheet.subsurface(rect)
    return _split_strip(cropped, scale, frame_count)


def load_image_region(path, filename, region, output_size=None):
    full_path = image_path(path, filename)
    sheet = pygame.image.load(full_path).convert_alpha()
    rect = _parse_region(region, sheet.get_width(), sheet.get_height())
    cropped = sheet.subsurface(rect)
    cropped = _trim_and_key_frame(cropped)
    if output_size:
        cropped = pygame.transform.smoothscale(cropped, output_size)
    return cropped


def _trim_and_key_frame(surface):
    try:
        from PIL import Image
    except Exception:
        return surface

    width, height = surface.get_width(), surface.get_height()
    if width < 2 or height < 2:
        return surface

    try:
        rgb_raw = pygame.image.tostring(surface, "RGB")
        img = Image.frombytes("RGB", (width, height), rgb_raw)
        pix = img.load()
    except Exception:
        return surface

    c0 = pix[0, 0]
    c1 = pix[width - 1, 0]
    c2 = pix[0, height - 1]
    c3 = pix[width - 1, height - 1]
    bg = (
        (c0[0] + c1[0] + c2[0] + c3[0]) // 4,
        (c0[1] + c1[1] + c2[1] + c3[1]) // 4,
        (c0[2] + c1[2] + c2[2] + c3[2]) // 4,
    )

    threshold = 52
    y_scan_start = int(height * 0.10)
    x_min = width
    y_min = height
    x_max = -1
    y_max = -1

    for y in range(y_scan_start, height):
        for x in range(width):
            r, g, b = pix[x, y]
            diff = abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2])
            if diff > threshold:
                if x < x_min:
                    x_min = x
                if y < y_min:
                    y_min = y
                if x > x_max:
                    x_max = x
                if y > y_max:
                    y_max = y

    if x_max < x_min or y_max < y_min:
        return surface

    pad = 2
    x0 = max(0, x_min - pad)
    y0 = max(0, y_min - pad)
    x1 = min(width - 1, x_max + pad)
    y1 = min(height - 1, y_max + pad)
    trimmed = surface.subsurface(pygame.Rect(x0, y0, x1 - x0 + 1, y1 - y0 + 1)).copy()

    # Apply chroma-like transparency based on detected background color.
    try:
        rgba_raw = pygame.image.tostring(trimmed, "RGBA")
        out = Image.frombytes("RGBA", trimmed.get_size(), rgba_raw)
        out_pix = out.load()
        tw, th = trimmed.get_size()
        alpha_threshold = 48
        for y in range(th):
            for x in range(tw):
                r, g, b, a = out_pix[x, y]
                diff = abs(r - bg[0]) + abs(g - bg[1]) + abs(b - bg[2])
                if diff < alpha_threshold:
                    out_pix[x, y] = (r, g, b, 0)
        trimmed = pygame.image.fromstring(out.tobytes(), out.size, "RGBA").convert_alpha()
    except Exception:
        pass

    return trimmed
