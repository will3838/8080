from __future__ import annotations

from pathlib import Path
from typing import Iterable

import imageio.v2 as imageio
import numpy as np
from PIL import Image, ImageDraw

from loot_table import Item


WIDTH = 1280
HEIGHT = 720
DURATION_SECONDS = 8
FPS = 24


def _fit_cover(image: Image.Image, w: int, h: int) -> Image.Image:
    src_w, src_h = image.size
    scale = max(w / src_w, h / src_h)
    new_w, new_h = int(src_w * scale), int(src_h * scale)
    resized = image.resize((new_w, new_h), Image.Resampling.LANCZOS)
    left = (new_w - w) // 2
    top = (new_h - h) // 2
    return resized.crop((left, top, left + w, top + h))


def _default_background() -> Image.Image:
    bg = Image.new("RGB", (WIDTH, HEIGHT), (22, 24, 35))
    draw = ImageDraw.Draw(bg)
    for y in range(HEIGHT):
        blend = y / HEIGHT
        color = (
            int(22 + (50 - 22) * blend),
            int(24 + (74 - 24) * blend),
            int(35 + (120 - 35) * blend),
        )
        draw.line((0, y, WIDTH, y), fill=color)
    return bg


def _default_frame(slot_w: int, slot_h: int) -> Image.Image:
    frame = Image.new("RGBA", (slot_w + 20, slot_h + 20), (0, 0, 0, 0))
    draw = ImageDraw.Draw(frame)
    draw.rounded_rectangle((0, 0, slot_w + 19, slot_h + 19), radius=20, outline=(255, 215, 0, 255), width=6)
    draw.rounded_rectangle((8, 8, slot_w + 11, slot_h + 11), radius=14, outline=(255, 255, 255, 180), width=3)
    return frame


def generate_spin_animation(
    items: Iterable[Item],
    output_path: Path,
    background_path: Path,
    frame_path: Path,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    slot_w, slot_h = 120, 120
    lane_y = HEIGHT // 2 - slot_h // 2
    visible_slots = 9
    spacing = 18
    step = slot_w + spacing

    item_list = list(items)
    if not item_list:
        raise ValueError("No items provided for animation")

    icon_cache: list[Image.Image] = []
    for item in item_list:
        icon = Image.open(item.icon_path).convert("RGBA")
        icon_cache.append(_fit_cover(icon, slot_w, slot_h))

    background = (
        Image.open(background_path).convert("RGB").resize((WIDTH, HEIGHT), Image.Resampling.LANCZOS)
        if background_path.exists()
        else _default_background()
    )

    frame_img = (
        Image.open(frame_path).convert("RGBA")
        if frame_path.exists()
        else _default_frame(slot_w, slot_h)
    )

    frames = DURATION_SECONDS * FPS
    start_offset = 0.0
    end_offset = step * (len(item_list) * 4 + 6)
    x_center = WIDTH // 2 - slot_w // 2

    with imageio.get_writer(output_path.as_posix(), fps=FPS, codec="libx264", quality=8, pixelformat="yuv420p") as writer:
        for idx in range(frames):
            t = idx / max(1, frames - 1)
            eased = 1 - (1 - t) ** 3
            offset = start_offset + (end_offset - start_offset) * eased

            frame = background.copy().convert("RGBA")

            for pos in range(-2, visible_slots + 4):
                lane_pos = pos * step - int(offset)
                x = x_center + lane_pos
                if x < -slot_w or x > WIDTH:
                    continue
                icon_idx = (int((offset / step) + pos)) % len(icon_cache)
                frame.alpha_composite(icon_cache[icon_idx], (x, lane_y))

            frame.alpha_composite(frame_img, (WIDTH // 2 - frame_img.width // 2, HEIGHT // 2 - frame_img.height // 2))
            writer.append_data(np.asarray(frame.convert("RGB")))
