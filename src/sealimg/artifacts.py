"""Manifest, hashing, README, and bundle artifact helpers."""

from __future__ import annotations

import hashlib
import json
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .crypto import sign_file
from .manifest import ManifestV1


@dataclass(frozen=True)
class PackageReadmeContext:
    image_id: str
    author: str
    website: str
    license: str
    master_filename: str
    web_filename: str


def sha256_file(path: Path) -> str:
    hasher = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def write_sha256_file(output_path: Path, files: dict[str, Path]) -> None:
    lines: list[str] = []
    for key in sorted(files):
        path = files[key]
        lines.append(f"{sha256_file(path)}  {path.name}")
    output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def compute_sha256_map(files: dict[str, Path]) -> dict[str, str]:
    return {key: sha256_file(path) for key, path in files.items()}


def update_manifest_file_hashes(
    manifest_payload: dict[str, Any],
    *,
    master_path: Path,
    web_path: Path,
) -> dict[str, Any]:
    updated = json.loads(json.dumps(manifest_payload))
    files = updated.setdefault("files", {})
    files.setdefault("master", {})
    files.setdefault("web", {})
    files["master"]["path"] = master_path.name
    files["master"]["sha256"] = sha256_file(master_path)
    files["web"]["path"] = web_path.name
    files["web"]["sha256"] = sha256_file(web_path)
    return updated


def stable_json_dumps(payload: dict[str, Any]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True) + "\n"


def write_manifest(path: Path, manifest: ManifestV1 | dict[str, Any]) -> None:
    payload = manifest.to_dict() if isinstance(manifest, ManifestV1) else manifest
    path.write_text(stable_json_dumps(payload), encoding="utf-8")


def sign_manifest(
    manifest_path: Path,
    signature_path: Path,
    private_key_path: Path,
    passphrase: str,
) -> None:
    sign_file(
        input_path=manifest_path,
        signature_path=signature_path,
        private_key_path=private_key_path,
        passphrase=passphrase,
    )


def render_package_readme(ctx: PackageReadmeContext) -> str:
    return (
        "SEALIMG - SEALED ARTWORK PACKAGE\n\n"
        f"Image ID: {ctx.image_id}\n"
        f"Author: {ctx.author}\n"
        f"Website: {ctx.website}\n"
        f"License: {ctx.license}\n\n"
        "Files:\n"
        f"- {ctx.master_filename} (lossless/pixel-preserving master; metadata embedded)\n"
        f"- {ctx.web_filename} (web export; visible watermark may be present)\n"
        "- manifest.json (human-readable provenance record)\n"
        "- manifest.sig (digital signature for manifest.json)\n"
        "- sha256.txt (file fingerprints)\n\n"
        "Verification:\n"
        "1) Check manifest signature with the author's public key.\n"
        "2) Compare file SHA-256 values to those in manifest.json.\n"
        "3) Some viewers may show provenance badges if supported.\n\n"
        "Notes:\n"
        "- Metadata may be stripped by some platforms; "
        "the signed manifest remains the source of truth.\n"
    )


def write_package_readme(path: Path, ctx: PackageReadmeContext) -> None:
    path.write_text(render_package_readme(ctx), encoding="utf-8")


def create_provenance_zip(zip_path: Path, files: list[Path]) -> None:
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, mode="w", compression=zipfile.ZIP_DEFLATED) as zf:
        for file_path in files:
            zf.write(file_path, arcname=file_path.name)
