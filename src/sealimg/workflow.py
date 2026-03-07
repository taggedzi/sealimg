"""Workflow orchestration for seal/verify/inspect commands."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from PIL import Image

from .artifacts import (
    PackageReadmeContext,
    create_provenance_zip,
    sha256_file,
    sign_manifest,
    update_manifest_file_hashes,
    write_manifest,
    write_package_readme,
    write_sha256_file,
)
from .c2pa import EmbedStatus, attempt_embed_claim, inspect_embed_status
from .config import SealimgConfig
from .crypto import public_key_fingerprint, verify_file
from .ids import ImageIdGenerator
from .image_pipeline import WebExportOptions, create_master_copy, create_web_copy, detect_format
from .manifest import MANIFEST_SCHEMA_V1, ManifestV1
from .metadata import MetadataFields, has_xmp
from .profiles import merge_profile


@dataclass(frozen=True)
class SealResult:
    input_path: Path
    image_id: str
    output_dir: Path
    master_path: Path
    web_path: Path
    manifest_path: Path
    signature_path: Path
    sha_path: Path
    readme_path: Path
    zip_path: Path | None
    master_embed_status: EmbedStatus
    web_embed_status: EmbedStatus


@dataclass(frozen=True)
class VerifyResult:
    manifest_path: Path
    signature_valid: bool
    key_id_match: bool
    hash_valid: bool
    master_embed_status: EmbedStatus
    web_embed_status: EmbedStatus
    sidecar_available: bool


@dataclass(frozen=True)
class InspectResult:
    path: Path
    format: str
    width: int
    height: int
    has_xmp: bool
    embed_status: EmbedStatus
    artifact_embed_statuses: dict[str, EmbedStatus]
    sidecar_available: bool


def discover_input_images(paths: list[Path], recursive: bool) -> list[Path]:
    out: list[Path] = []
    for path in paths:
        if path.is_file():
            out.append(path)
            continue
        if not path.is_dir():
            continue
        if recursive:
            candidates = sorted(p for p in path.rglob("*") if p.is_file())
        else:
            candidates = sorted(p for p in path.iterdir() if p.is_file())
        for candidate in candidates:
            if candidate.suffix.lower() in {".png", ".jpg", ".jpeg"}:
                out.append(candidate)
    return out


def seal_image(
    *,
    input_path: Path,
    output_root: Path,
    id_generator: ImageIdGenerator,
    metadata: MetadataFields,
    profile_defaults: dict[str, Any],
    selected_profile: dict[str, Any],
    cli_overrides: dict[str, Any],
    bundle: bool,
    embed_enabled: bool,
    signing_key_path: Path,
    passphrase: str,
    signer_name: str,
    public_key_path: Path,
    image_id_override: str | None = None,
) -> SealResult:
    detect_format(input_path)
    image_id = image_id_override or id_generator.next_id()
    output_dir = output_root / image_id
    output_dir.mkdir(parents=True, exist_ok=True)

    source_ext = ".jpg" if input_path.suffix.lower() in {".jpg", ".jpeg"} else ".png"
    master_path = output_dir / f"master{source_ext}"
    web_path = output_dir / "web.jpg"
    manifest_path = output_dir / "manifest.json"
    signature_path = output_dir / "manifest.sig"
    sha_path = output_dir / "sha256.txt"
    readme_path = output_dir / "README.txt"
    zip_path = output_dir / "provenance.zip" if bundle else None

    merged = merge_profile(profile_defaults, selected_profile, cli_overrides)
    invisible_enabled = bool(merged.get("wm_invisible", {}).get("enabled", False))
    invisible_payload = _resolve_invisible_payload(merged, image_id, invisible_enabled)
    create_master_copy(input_path=input_path, output_path=master_path, metadata_fields=metadata)
    create_web_copy(
        input_path=input_path,
        output_path=web_path,
        metadata_fields=metadata,
        options=WebExportOptions(
            long_edge=int(merged.get("long_edge", 2560)),
            jpeg_quality=int(merged.get("jpeg_quality", 82)),
            visible_watermark_enabled=bool(merged.get("wm_visible", {}).get("enabled", True)),
            visible_watermark_text=str(merged.get("wm_visible", {}).get("text", "")),
            visible_watermark_style=str(merged.get("wm_visible", {}).get("style", "diag-low")),
            invisible_watermark_enabled=invisible_enabled,
            invisible_watermark_payload=invisible_payload,
        ),
    )
    master_embed_status = attempt_embed_claim(master_path, manifest_path, enabled=embed_enabled)
    web_embed_status = attempt_embed_claim(web_path, manifest_path, enabled=embed_enabled)

    signer_key_id = public_key_fingerprint(public_key_path.read_bytes())
    manifest_payload = {
        "schema": MANIFEST_SCHEMA_V1,
        "image_id": image_id,
        "author": metadata.author,
        "website": metadata.website,
        "license": metadata.license,
        "files": {
            "master": {"path": master_path.name, "sha256": ""},
            "web": {"path": web_path.name, "sha256": ""},
        },
        "timestamps": {
            "local_created": datetime.now().astimezone().isoformat(timespec="seconds"),
            "sealed_utc": datetime.now(timezone.utc)
            .isoformat(timespec="seconds")
            .replace("+00:00", "Z"),
        },
        "watermarks": {
            "visible": {
                "applied": bool(merged.get("wm_visible", {}).get("enabled", True)),
                "style": str(merged.get("wm_visible", {}).get("style", "diag-low")),
                "text": str(merged.get("wm_visible", {}).get("text", "")),
            },
            "invisible": {
                "applied": invisible_enabled,
                "payload": invisible_payload,
            },
        },
        "signature": {
            "algo": "rsa" if "rsa" in signing_key_path.name.lower() else "ed25519",
            "signer": signer_name,
            "signer_display": signer_name,
            "signer_key_id": signer_key_id,
            "pubkey_fingerprint": signer_key_id,
            "signature_file": signature_path.name,
        },
    }
    manifest_payload = update_manifest_file_hashes(
        manifest_payload, master_path=master_path, web_path=web_path
    )
    manifest = ManifestV1.from_dict(manifest_payload)
    write_manifest(manifest_path, manifest)
    sign_manifest(manifest_path, signature_path, signing_key_path, passphrase)
    write_sha256_file(sha_path, {"master": master_path, "web": web_path, "manifest": manifest_path})
    write_package_readme(
        readme_path,
        PackageReadmeContext(
            image_id=image_id,
            author=metadata.author,
            website=metadata.website,
            license=metadata.license,
            master_filename=master_path.name,
            web_filename=web_path.name,
        ),
    )

    if zip_path is not None:
        create_provenance_zip(
            zip_path,
            [master_path, web_path, manifest_path, signature_path, sha_path, readme_path],
        )
    return SealResult(
        input_path=input_path,
        image_id=image_id,
        output_dir=output_dir,
        master_path=master_path,
        web_path=web_path,
        manifest_path=manifest_path,
        signature_path=signature_path,
        sha_path=sha_path,
        readme_path=readme_path,
        zip_path=zip_path,
        master_embed_status=master_embed_status,
        web_embed_status=web_embed_status,
    )


def resolve_manifest_from_target(target: Path) -> Path:
    if target.name == "manifest.json":
        return target
    local = target.parent / "manifest.json"
    if local.exists():
        return local
    raise FileNotFoundError("manifest.json not found alongside target")


def verify_target(target: Path, public_key_path: Path) -> VerifyResult:
    manifest_path = resolve_manifest_from_target(target)
    payload = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest = ManifestV1.from_dict(payload)
    sig_path = manifest_path.with_name(manifest.signature["signature_file"])

    expected_key_id = manifest.signature.get("signer_key_id") or manifest.signature.get(
        "pubkey_fingerprint"
    )
    actual_key_id = public_key_fingerprint(public_key_path.read_bytes())
    key_id_match = expected_key_id == actual_key_id
    signature_valid = key_id_match and verify_file(manifest_path, sig_path, public_key_path)
    master = manifest_path.parent / manifest.files["master"]["path"]
    web = manifest_path.parent / manifest.files["web"]["path"]
    hash_valid = (
        master.exists()
        and web.exists()
        and sha256_file(master) == manifest.files["master"]["sha256"]
        and sha256_file(web) == manifest.files["web"]["sha256"]
    )
    sidecar_available = manifest_path.exists() and sig_path.exists()
    master_embed_status = _inspect_artifact_embed_status(master)
    web_embed_status = _inspect_artifact_embed_status(web)
    return VerifyResult(
        manifest_path=manifest_path,
        signature_valid=signature_valid,
        key_id_match=key_id_match,
        hash_valid=hash_valid,
        master_embed_status=master_embed_status,
        web_embed_status=web_embed_status,
        sidecar_available=sidecar_available,
    )


def inspect_image(path: Path) -> InspectResult:
    fmt = detect_format(path)
    with Image.open(path) as image:
        width, height = image.size
    sidecar_path = path.parent / "manifest.json"
    artifact_embed_statuses: dict[str, EmbedStatus]
    sidecar_available = sidecar_path.exists()
    if sidecar_available:
        artifact_embed_statuses = _inspect_embed_statuses_from_manifest(sidecar_path)
    else:
        artifact_embed_statuses = {"input": inspect_embed_status(path)}
    return InspectResult(
        path=path,
        format=fmt,
        width=width,
        height=height,
        has_xmp=has_xmp(path),
        embed_status=inspect_embed_status(path),
        artifact_embed_statuses=artifact_embed_statuses,
        sidecar_available=sidecar_available,
    )


def derive_paths_from_config(
    config: SealimgConfig,
    *,
    signing_key_override: str | None,
) -> tuple[Path, Path]:
    signing_key = Path(signing_key_override or config.signing_key).expanduser()
    if signing_key.exists():
        candidate = signing_key.with_suffix(".pub")
        if candidate.exists():
            return signing_key, candidate
    raise FileNotFoundError("Unable to resolve signing key and matching public key")


def _inspect_artifact_embed_status(path: Path) -> EmbedStatus:
    if not path.exists():
        return EmbedStatus(status="missing", message=f"Artifact missing: {path.name}")
    return inspect_embed_status(path)


def _inspect_embed_statuses_from_manifest(manifest_path: Path) -> dict[str, EmbedStatus]:
    try:
        payload = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest = ManifestV1.from_dict(payload)
    except Exception:
        return {"input": _inspect_artifact_embed_status(manifest_path)}

    base = manifest_path.parent
    master = base / manifest.files["master"]["path"]
    web = base / manifest.files["web"]["path"]
    return {
        "master": _inspect_artifact_embed_status(master),
        "web": _inspect_artifact_embed_status(web),
    }


def _resolve_invisible_payload(
    merged_profile: dict[str, Any],
    image_id: str,
    enabled: bool,
) -> str | None:
    wm_invisible = merged_profile.get("wm_invisible", {})
    raw_payload = wm_invisible.get("payload")
    if not enabled:
        if raw_payload in (None, ""):
            return None
        return str(raw_payload)
    if raw_payload in (None, ""):
        return image_id
    return str(raw_payload)
