"""Manifest v1 domain model and validation."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any


class ManifestError(ValueError):
    """Raised when manifest content is invalid."""


MANIFEST_SCHEMA_V1 = "https://sealimg.org/provenance/v1"


@dataclass(frozen=True)
class ManifestV1:
    schema: str
    image_id: str
    author: str
    website: str
    license: str
    files: dict[str, dict[str, str]]
    timestamps: dict[str, str]
    signature: dict[str, str]
    title: str | None = None
    notes: str | None = None
    source: dict[str, Any] | None = None
    watermarks: dict[str, Any] | None = None
    links: list[str] | None = None

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "ManifestV1":
        allowed = {
            "schema",
            "image_id",
            "author",
            "website",
            "license",
            "files",
            "timestamps",
            "signature",
            "title",
            "notes",
            "source",
            "watermarks",
            "links",
        }
        unknown = sorted(set(payload.keys()) - allowed)
        if unknown:
            raise ManifestError(f"Unknown manifest fields: {', '.join(unknown)}")

        required = {
            "schema": str,
            "image_id": str,
            "author": str,
            "website": str,
            "license": str,
            "files": dict,
            "timestamps": dict,
            "signature": dict,
        }
        missing = [k for k in required if k not in payload]
        if missing:
            raise ManifestError(f"Missing required manifest fields: {', '.join(missing)}")
        for field, expected in required.items():
            if not isinstance(payload[field], expected):
                raise ManifestError(f"Manifest field '{field}' must be {expected.__name__}")

        if payload["schema"] != MANIFEST_SCHEMA_V1:
            raise ManifestError(f"Unsupported manifest schema: {payload['schema']}")

        _validate_files(payload["files"])
        _validate_timestamps(payload["timestamps"])
        _validate_signature(payload["signature"])

        links = payload.get("links")
        if links is not None:
            if not isinstance(links, list) or any(not isinstance(item, str) for item in links):
                raise ManifestError("Manifest field 'links' must be a list of strings")

        for maybe_dict in ("source", "watermarks"):
            value = payload.get(maybe_dict)
            if value is not None and not isinstance(value, dict):
                raise ManifestError(f"Manifest field '{maybe_dict}' must be an object")

        for maybe_str in ("title", "notes"):
            value = payload.get(maybe_str)
            if value is not None and not isinstance(value, str):
                raise ManifestError(f"Manifest field '{maybe_str}' must be a string")

        return cls(
            schema=payload["schema"],
            image_id=payload["image_id"],
            author=payload["author"],
            website=payload["website"],
            license=payload["license"],
            files=payload["files"],
            timestamps=payload["timestamps"],
            signature=payload["signature"],
            title=payload.get("title"),
            notes=payload.get("notes"),
            source=payload.get("source"),
            watermarks=payload.get("watermarks"),
            links=links,
        )

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "schema": self.schema,
            "image_id": self.image_id,
            "author": self.author,
            "website": self.website,
            "license": self.license,
            "files": self.files,
            "timestamps": self.timestamps,
            "signature": self.signature,
        }
        if self.title is not None:
            payload["title"] = self.title
        if self.notes is not None:
            payload["notes"] = self.notes
        if self.source is not None:
            payload["source"] = self.source
        if self.watermarks is not None:
            payload["watermarks"] = self.watermarks
        if self.links is not None:
            payload["links"] = self.links
        return payload


def _validate_files(files: dict[str, Any]) -> None:
    for key in ("master", "web"):
        if key not in files or not isinstance(files[key], dict):
            raise ManifestError(f"Manifest files.{key} must be an object")
        entry = files[key]
        for required in ("path", "sha256"):
            if required not in entry or not isinstance(entry[required], str):
                raise ManifestError(f"Manifest files.{key}.{required} must be a string")


def _validate_timestamps(timestamps: dict[str, Any]) -> None:
    for key in ("local_created", "sealed_utc"):
        if key not in timestamps or not isinstance(timestamps[key], str):
            raise ManifestError(f"Manifest timestamps.{key} must be a string")
    _validate_iso8601(timestamps["local_created"], "timestamps.local_created")
    _validate_iso8601(timestamps["sealed_utc"], "timestamps.sealed_utc")

    if "public_proof" in timestamps and timestamps["public_proof"] is not None:
        if not isinstance(timestamps["public_proof"], str):
            raise ManifestError("Manifest timestamps.public_proof must be a string")


def _validate_signature(signature: dict[str, Any]) -> None:
    for key in ("algo", "signer", "pubkey_fingerprint", "signature_file"):
        if key not in signature or not isinstance(signature[key], str):
            raise ManifestError(f"Manifest signature.{key} must be a string")


def _validate_iso8601(value: str, field_name: str) -> None:
    normalized = value.replace("Z", "+00:00")
    try:
        datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ManifestError(f"{field_name} is not valid ISO-8601: {value}") from exc
