"""C2PA embedding helpers and status reporting."""

from __future__ import annotations

import struct
import zlib
from dataclasses import dataclass
from pathlib import Path

JUMBF_PREFIX = b"JUMBF\x00SEALIMG\x00"
PNG_C2PA_KEYWORD = b"c2pa.manifest"


@dataclass(frozen=True)
class EmbedStatus:
    status: str
    message: str


def attempt_embed_claim(image_path: Path, manifest_path: Path, enabled: bool = True) -> EmbedStatus:
    if not enabled:
        return EmbedStatus(status="skipped", message="Embedding disabled by --no-embed.")

    ext = image_path.suffix.lower()
    try:
        if ext in {".jpg", ".jpeg"}:
            _embed_jpeg_app11(image_path, manifest_path)
            return EmbedStatus(status="embedded", message="Embedded C2PA marker in JPEG APP11.")
        if ext == ".png":
            _embed_png_chunk(image_path, manifest_path)
            return EmbedStatus(
                status="embedded",
                message="Embedded C2PA marker in PNG ancillary chunk.",
            )
    except Exception as exc:
        return EmbedStatus(
            status="failed",
            message=f"Embedding failed ({exc}); sidecar manifest remains canonical.",
        )
    return EmbedStatus(status="unsupported", message=f"Unsupported format for embed: {ext}")


def inspect_embed_status(image_path: Path) -> EmbedStatus:
    ext = image_path.suffix.lower()
    data = image_path.read_bytes()
    if ext in {".jpg", ".jpeg"} and JUMBF_PREFIX in data:
        return EmbedStatus(status="detected", message="Embedded JPEG APP11 C2PA marker detected.")
    if ext == ".png" and PNG_C2PA_KEYWORD in data:
        return EmbedStatus(status="detected", message="Embedded PNG C2PA chunk detected.")
    return EmbedStatus(status="none", message="No embedded C2PA markers detected.")


def _embed_jpeg_app11(image_path: Path, manifest_path: Path) -> None:
    data = image_path.read_bytes()
    if len(data) < 4 or data[0:2] != b"\xff\xd8":
        raise ValueError("invalid jpeg file")

    payload = JUMBF_PREFIX + manifest_path.name.encode("utf-8")
    seg_len = len(payload) + 2
    if seg_len > 65535:
        raise ValueError("c2pa payload too large")
    segment = b"\xff\xeb" + struct.pack(">H", seg_len) + payload

    out = bytearray()
    out.extend(data[:2])  # SOI
    out.extend(segment)

    i = 2
    while i < len(data):
        if data[i] != 0xFF:
            out.extend(data[i:])
            break
        marker = data[i + 1]
        if marker == 0xDA:  # SOS
            out.extend(data[i:])
            break
        if marker in {0xD8, 0xD9} or 0xD0 <= marker <= 0xD7:
            out.extend(data[i : i + 2])
            i += 2
            continue
        if i + 4 > len(data):
            raise ValueError("truncated jpeg")
        length = struct.unpack(">H", data[i + 2 : i + 4])[0]
        end = i + 2 + length
        if end > len(data):
            raise ValueError("truncated jpeg segment")
        existing = data[i:end]
        seg_payload = existing[4:]
        is_ours = marker == 0xEB and seg_payload.startswith(JUMBF_PREFIX)
        if not is_ours:
            out.extend(existing)
        i = end

    image_path.write_bytes(bytes(out))


def _embed_png_chunk(image_path: Path, manifest_path: Path) -> None:
    data = image_path.read_bytes()
    png_sig = b"\x89PNG\r\n\x1a\n"
    if not data.startswith(png_sig):
        raise ValueError("invalid png file")

    payload_text = f'{{"manifest":"{manifest_path.name}"}}'.encode("utf-8")
    itxt_data = PNG_C2PA_KEYWORD + b"\x00\x00\x00\x00\x00" + payload_text
    c2pa_chunk = _make_png_chunk(b"iTXt", itxt_data)

    chunks: list[bytes] = []
    i = len(png_sig)
    while i < len(data):
        if i + 8 > len(data):
            raise ValueError("truncated png chunk header")
        length = struct.unpack(">I", data[i : i + 4])[0]
        chunk_type = data[i + 4 : i + 8]
        start = i + 8
        end = start + length
        crc_end = end + 4
        if crc_end > len(data):
            raise ValueError("truncated png chunk")
        chunk_data = data[start:end]
        keep = True
        if chunk_type == b"iTXt":
            keyword = chunk_data.split(b"\x00", 1)[0]
            if keyword == PNG_C2PA_KEYWORD:
                keep = False
        if keep:
            chunks.append(data[i:crc_end])
        i = crc_end

    out = bytearray(png_sig)
    inserted = False
    for raw in chunks:
        ctype = raw[4:8]
        if ctype == b"IEND" and not inserted:
            out.extend(c2pa_chunk)
            inserted = True
        out.extend(raw)

    if not inserted:
        out.extend(c2pa_chunk)
        out.extend(_make_png_chunk(b"IEND", b""))
    image_path.write_bytes(bytes(out))


def _make_png_chunk(chunk_type: bytes, chunk_data: bytes) -> bytes:
    length = struct.pack(">I", len(chunk_data))
    crc = struct.pack(">I", zlib.crc32(chunk_type + chunk_data) & 0xFFFFFFFF)
    return length + chunk_type + chunk_data + crc
