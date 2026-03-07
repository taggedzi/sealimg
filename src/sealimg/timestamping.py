"""Timestamp helper utilities."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from urllib import request

from .artifacts import sha256_file


def build_hash_line(manifest_path: Path, image_id: str) -> str:
    ts = datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    digest = sha256_file(manifest_path)
    return f"{ts}  {image_id}  {digest}"


def append_hash_line(log_path: Path, line: str) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as handle:
        handle.write(line + "\n")


def post_hash_line(url: str, line: str, timeout_seconds: int = 5) -> None:
    payload = line.encode("utf-8")
    req = request.Request(url=url, data=payload, method="POST")
    req.add_header("Content-Type", "text/plain; charset=utf-8")
    with request.urlopen(req, timeout=timeout_seconds):
        return
