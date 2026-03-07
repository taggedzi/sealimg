"""Perceptual hash helpers for v0.7 similarity reporting."""

from __future__ import annotations

import math
from pathlib import Path

from .image_pipeline import ImagePipelineError, _require_pillow


def compute_phash(path: Path, hash_size: int = 8, highfreq_factor: int = 4) -> str:
    p = _require_pillow()
    image_mod = p["Image"]
    size = hash_size * highfreq_factor

    with image_mod.open(path) as image:
        sample = image.convert("L").resize((size, size), resample=image_mod.Resampling.LANCZOS)

    pixels = list(sample.tobytes())
    matrix = [pixels[i * size : (i + 1) * size] for i in range(size)]
    dct = _dct_2d(matrix)
    block = [row[:hash_size] for row in dct[:hash_size]]
    values = [v for row in block for v in row]
    median = _median(values[1:]) if len(values) > 1 else values[0]

    bits = [1 if value >= median else 0 for value in values]
    return _bits_to_hex(bits)


def _dct_2d(values: list[list[float]]) -> list[list[float]]:
    n = len(values)
    if n == 0 or any(len(row) != n for row in values):
        raise ImagePipelineError("invalid matrix for dct")

    cos_table = [
        [math.cos((math.pi * (2 * x + 1) * u) / (2 * n)) for x in range(n)] for u in range(n)
    ]
    alpha = [math.sqrt(1 / n)] + [math.sqrt(2 / n)] * (n - 1)

    row_dct = [[0.0 for _ in range(n)] for _ in range(n)]
    for y in range(n):
        for u in range(n):
            row_dct[y][u] = alpha[u] * sum(values[y][x] * cos_table[u][x] for x in range(n))

    out = [[0.0 for _ in range(n)] for _ in range(n)]
    for v in range(n):
        for u in range(n):
            out[v][u] = alpha[v] * sum(row_dct[y][u] * cos_table[v][y] for y in range(n))
    return out


def _median(values: list[float]) -> float:
    ordered = sorted(values)
    mid = len(ordered) // 2
    if len(ordered) % 2 == 1:
        return ordered[mid]
    return (ordered[mid - 1] + ordered[mid]) / 2.0


def _bits_to_hex(bits: list[int]) -> str:
    out: list[str] = []
    for i in range(0, len(bits), 4):
        nibble = bits[i : i + 4]
        while len(nibble) < 4:
            nibble.append(0)
        value = (nibble[0] << 3) | (nibble[1] << 2) | (nibble[2] << 1) | nibble[3]
        out.append(f"{value:x}")
    return "".join(out)
