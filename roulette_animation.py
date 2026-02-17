from __future__ import annotations

import random
from pathlib import Path
from typing import Dict, List

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw, ImageOps

from loot_table import LootItem


WIDTH = 1280
HEIGHT = 720
FPS = 24
DURATION_SECONDS = 8


def _cover_resize(img: Image.Image, target_w: int, target_h: int) -> Image.Image:
    return ImageOps.fit(img.convert("RGBA"), (target_w, target_h), method=Image.Resampling.LANCZOS)


def generate_spin_animation(items: List[LootItem], out_path: Path) -> None:
    if out_path.exists():
        return

    out_path.parent.mkdir(parents=True, exist_ok=True)

    tile = 170
    visible = 9
    strip_w = tile * visible
    strip_h = tile
    strip_x = (WIDTH - strip_w) // 2
    strip_y = (HEIGHT - strip_h) // 2

    background = _build_background()
    frame_overlay = _build_frame(tile, strip_x, strip_y)

    icon_cache: Dict[str, Image.Image] = {}
    for item in items:
        with Image.open(item.icon_path) as src:
            icon_cache[item.item_id] = _cover_resize(src, tile, tile)

    sequence = [random.choice(items) for _ in range(160)]

    writer = imageio.get_writer(
        out_path,
        format="ffmpeg",
        fps=FPS,
        codec="libx264",
        quality=6,
        pixelformat="yuv420p",
        macro_block_size=16,
    )

    total_frames = FPS * DURATION_SECONDS
    start_offset = 0.0
    end_offset = tile * (len(sequence) - visible - 2)

    try:
        for frame_idx in range(total_frames):
            t = frame_idx / float(total_frames - 1)
            eased = 1.0 - pow(1.0 - t, 3)
            offset = start_offset + (end_offset - start_offset) * eased

            canvas = background.copy()
            draw = ImageDraw.Draw(canvas)

            draw.rounded_rectangle(
                (strip_x - 16, strip_y - 16, strip_x + strip_w + 16, strip_y + strip_h + 16),
                radius=26,
                fill=(20, 20, 28, 200),
            )

            first_idx = int(offset // tile)
            sub = int(offset % tile)
            x_cursor = strip_x - sub

            for idx in range(first_idx, first_idx + visible + 2):
                if idx < 0 or idx >= len(sequence):
                    continue
                item = sequence[idx]
                icon = icon_cache[item.item_id]
                canvas.alpha_composite(icon, (x_cursor, strip_y))
                x_cursor += tile

            canvas.alpha_composite(frame_overlay)
            writer.append_data(np.array(canvas.convert("RGB"), dtype=np.uint8))
    finally:
        writer.close()


def _build_background() -> Image.Image:
    bg_path = Path("assets/background.png")
    if bg_path.exists():
        with Image.open(bg_path) as img:
            return _cover_resize(img, WIDTH, HEIGHT)

    img = Image.new("RGBA", (WIDTH, HEIGHT), (30, 35, 50, 255))
    draw = ImageDraw.Draw(img)
    for y in range(HEIGHT):
        k = y / HEIGHT
        color = (
            int(22 + 25 * k),
            int(35 + 30 * k),
            int(60 + 70 * k),
            255,
        )
        draw.line((0, y, WIDTH, y), fill=color)
    return img


def _build_frame(tile: int, strip_x: int, strip_y: int) -> Image.Image:
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    frame_path = Path("assets/frame.png")

    if frame_path.exists():
        with Image.open(frame_path) as src:
            frame = _cover_resize(src, tile + 28, tile + 28)
    else:
        frame = Image.new("RGBA", (tile + 28, tile + 28), (0, 0, 0, 0))
        draw = ImageDraw.Draw(frame)
        draw.rounded_rectangle((0, 0, tile + 27, tile + 27), radius=18, outline=(255, 210, 90, 255), width=8)

    center_x = strip_x + (tile * 4) - 14
    center_y = strip_y - 14
    overlay.alpha_composite(frame, (center_x, center_y))
    return overlay
