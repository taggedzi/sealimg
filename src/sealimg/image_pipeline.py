"""PNG/JPEG processing pipeline for master and web outputs."""

from __future__ import annotations

import hashlib
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from .metadata import MetadataFields, build_xmp_packet, embed_xmp


class ImagePipelineError(RuntimeError):
    """Raised when image processing fails."""


def _require_pillow():
    try:
        from PIL import Image, ImageDraw, ImageFont
    except Exception as exc:  # pragma: no cover - depends on runtime environment
        raise ImagePipelineError("Pillow is required for image processing") from exc
    return {"Image": Image, "ImageDraw": ImageDraw, "ImageFont": ImageFont}


@dataclass(frozen=True)
class WebExportOptions:
    long_edge: int = 2560
    jpeg_quality: int = 82
    visible_watermark_enabled: bool = True
    visible_watermark_text: str = ""
    visible_watermark_style: str = "diag-low"
    invisible_watermark_enabled: bool = False
    invisible_watermark_payload: str | None = None


class InvisibleWatermarkProvider(Protocol):
    def apply(self, image: object, payload: str) -> object:  # pragma: no cover - interface only
        ...


class LsbInvisibleWatermarkProvider:
    """Lightweight deterministic LSB watermark for JPEG web exports."""

    def __init__(self, max_bits: int = 4096, strength: int = 4) -> None:
        self.max_bits = max_bits
        self.strength = max(1, strength)

    def apply(self, image: object, payload: str) -> object:
        width, height = image.size
        capacity = width * height
        if capacity == 0:
            return image

        bits = _payload_bits(payload)
        bit_count = min(self.max_bits, capacity)
        seed = int.from_bytes(hashlib.sha256(payload.encode("utf-8")).digest()[:8], "big")
        rng = random.Random(seed)
        pixels = image.load()

        used: set[tuple[int, int]] = set()
        bit_index = 0
        while len(used) < bit_count:
            x = rng.randrange(width)
            y = rng.randrange(height)
            if (x, y) in used:
                continue
            used.add((x, y))
            r, g, b = pixels[x, y]
            bit = bits[bit_index % len(bits)]
            if bit == 1:
                b = min(255, b + self.strength)
            else:
                b = max(0, b - self.strength)
            pixels[x, y] = (r, g, b)
            bit_index += 1
        return image


def detect_format(path: Path) -> str:
    ext = path.suffix.lower()
    if ext == ".png":
        return "png"
    if ext in {".jpg", ".jpeg"}:
        return "jpeg"
    raise ImagePipelineError(f"Unsupported image format: {ext}")


def create_master_copy(
    input_path: Path,
    output_path: Path,
    metadata_fields: MetadataFields,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    xmp = build_xmp_packet(metadata_fields)
    embed_xmp(input_path=input_path, output_path=output_path, xmp_packet=xmp)


def create_web_copy(
    input_path: Path,
    output_path: Path,
    metadata_fields: MetadataFields,
    options: WebExportOptions,
    invisible_provider: InvisibleWatermarkProvider | None = None,
) -> None:
    p = _require_pillow()
    image_mod = p["Image"]
    draw_mod = p["ImageDraw"]
    font_mod = p["ImageFont"]

    with image_mod.open(input_path) as original:
        image = original.convert("RGB")
        image = _resize_long_edge(image, options.long_edge, image_mod)

        if options.visible_watermark_enabled and options.visible_watermark_text:
            _apply_visible_watermark(
                image=image,
                text=options.visible_watermark_text,
                style=options.visible_watermark_style,
                draw_mod=draw_mod,
                font_mod=font_mod,
            )

        if (
            options.invisible_watermark_enabled
            and options.invisible_watermark_payload
        ):
            provider = invisible_provider or LsbInvisibleWatermarkProvider()
            image = provider.apply(image, options.invisible_watermark_payload)

        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path, format="JPEG", quality=options.jpeg_quality, optimize=True)

    xmp = build_xmp_packet(metadata_fields)
    embed_xmp(input_path=output_path, output_path=output_path, xmp_packet=xmp)


def _resize_long_edge(image: object, long_edge: int, image_mod: object) -> object:
    width, height = image.size
    current_long = max(width, height)
    if current_long <= long_edge:
        return image
    scale = long_edge / float(current_long)
    target = (max(1, int(round(width * scale))), max(1, int(round(height * scale))))
    return image.resize(target, resample=image_mod.Resampling.LANCZOS)


def _apply_visible_watermark(
    image: object,
    text: str,
    style: str,
    draw_mod: object,
    font_mod: object,
) -> None:
    draw = draw_mod.Draw(image, "RGBA")
    try:
        font = font_mod.load_default()
    except Exception:  # pragma: no cover
        font = None

    width, height = image.size
    if style == "diag-low":
        # Repeated diagonal watermark with low alpha for deterrence without heavy visual impact.
        step = max(160, min(width, height) // 3)
        for offset in range(-height, width, step):
            draw.text((offset, height - 70), text, fill=(255, 255, 255, 70), font=font)
    else:
        draw.text((20, height - 40), text, fill=(255, 255, 255, 80), font=font)


def _payload_bits(payload: str) -> list[int]:
    digest = hashlib.sha256(payload.encode("utf-8")).digest()
    bits: list[int] = []
    for byte in digest:
        for shift in range(7, -1, -1):
            bits.append((byte >> shift) & 1)
    return bits
