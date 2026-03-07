"""C2PA embedding stubs and status reporting."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class EmbedStatus:
    status: str
    message: str


def attempt_embed_claim(image_path: Path, manifest_path: Path, enabled: bool = True) -> EmbedStatus:
    if not enabled:
        return EmbedStatus(status="skipped", message="Embedding disabled by --no-embed.")

    ext = image_path.suffix.lower()
    if ext not in {".png", ".jpg", ".jpeg"}:
        return EmbedStatus(status="unsupported", message=f"Unsupported format for embed: {ext}")

    # v0.1 sidecar-first implementation: report non-blocking unsupported status.
    _ = manifest_path
    return EmbedStatus(
        status="unsupported",
        message="C2PA embedding adapter not implemented yet; sidecar manifest remains canonical.",
    )


def inspect_embed_status(image_path: Path) -> EmbedStatus:
    data = image_path.read_bytes()
    if b"c2pa" in data.lower() or b"jumbf" in data.lower():
        return EmbedStatus(
            status="detected",
            message="Potential embedded provenance markers detected.",
        )
    return EmbedStatus(status="none", message="No embedded C2PA markers detected.")
