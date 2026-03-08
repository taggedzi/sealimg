"""Configuration domain model and YAML helpers."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


class ConfigError(ValueError):
    """Raised when config content is invalid."""


@dataclass(frozen=True)
class SealimgConfig:
    author: str
    website: str
    license: str
    default_profile: str
    output_root: str
    signing_key: str
    artifact_naming: str = "source-id"
    revocations_file: str = "~/.sealimg/revocations.txt"
    profiles: dict[str, dict[str, Any]] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "SealimgConfig":
        required = {
            "author": str,
            "website": str,
            "license": str,
            "default_profile": str,
            "output_root": str,
            "signing_key": str,
            "profiles": dict,
        }
        missing = [k for k in required if k not in payload]
        if missing:
            raise ConfigError(f"Missing required config keys: {', '.join(missing)}")

        for key, expected in required.items():
            value = payload[key]
            if not isinstance(value, expected):
                raise ConfigError(f"Config key '{key}' must be {expected.__name__}")

        profiles_raw = payload["profiles"]
        profiles: dict[str, dict[str, Any]] = {}
        for name, data in profiles_raw.items():
            if not isinstance(name, str):
                raise ConfigError("Profile names must be strings")
            if not isinstance(data, dict):
                raise ConfigError(f"Profile '{name}' must be an object")
            profiles[name] = data

        if payload["default_profile"] not in profiles:
            raise ConfigError("default_profile must reference a profile in profiles")

        artifact_naming = str(payload.get("artifact_naming", "source-id")).strip().lower()
        if artifact_naming not in {"legacy", "source-id"}:
            raise ConfigError("artifact_naming must be one of: legacy, source-id")
        revocations_file = str(
            payload.get("revocations_file", "~/.sealimg/revocations.txt")
        ).strip()

        return cls(
            author=payload["author"],
            website=payload["website"],
            license=payload["license"],
            default_profile=payload["default_profile"],
            output_root=payload["output_root"],
            signing_key=payload["signing_key"],
            artifact_naming=artifact_naming,
            revocations_file=revocations_file,
            profiles=profiles,
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "author": self.author,
            "website": self.website,
            "license": self.license,
            "default_profile": self.default_profile,
            "output_root": self.output_root,
            "signing_key": self.signing_key,
            "artifact_naming": self.artifact_naming,
            "revocations_file": self.revocations_file,
            "profiles": self.profiles,
        }


def _parse_scalar(value: str) -> Any:
    text = value.strip()
    if text == "":
        return {}
    if text in {"true", "True"}:
        return True
    if text in {"false", "False"}:
        return False
    if text in {"null", "None"}:
        return None
    if text.startswith('"') and text.endswith('"'):
        return text[1:-1]
    if text.startswith("'") and text.endswith("'"):
        return text[1:-1]
    if text.isdigit():
        return int(text)
    return text


def parse_yaml_object(text: str) -> dict[str, Any]:
    """Parse a simple YAML mapping format used by config.yml."""
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]

    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        if "\t" in raw_line:
            raise ConfigError("Tabs are not supported in config YAML")

        indent = len(raw_line) - len(raw_line.lstrip(" "))
        if ":" not in raw_line:
            raise ConfigError(f"Invalid YAML line: {raw_line}")
        key_part, value_part = raw_line.strip().split(":", 1)
        key = key_part.strip()
        if not key:
            raise ConfigError(f"Invalid YAML key in line: {raw_line}")

        while stack and indent <= stack[-1][0]:
            stack.pop()
        if not stack:
            raise ConfigError("Invalid indentation in YAML")

        target = stack[-1][1]
        value = _parse_scalar(value_part)
        target[key] = value

        if value == {}:
            nested: dict[str, Any] = {}
            target[key] = nested
            stack.append((indent, nested))

    return root


def dump_yaml_object(data: dict[str, Any]) -> str:
    """Dump nested dictionaries to simple YAML."""

    def _emit(node: dict[str, Any], indent: int) -> list[str]:
        lines: list[str] = []
        prefix = " " * indent
        for key, value in node.items():
            if isinstance(value, dict):
                lines.append(f"{prefix}{key}:")
                lines.extend(_emit(value, indent + 2))
            elif isinstance(value, bool):
                lines.append(f"{prefix}{key}: {'true' if value else 'false'}")
            elif value is None:
                lines.append(f"{prefix}{key}: null")
            elif isinstance(value, int):
                lines.append(f"{prefix}{key}: {value}")
            else:
                escaped = str(value).replace('"', '\\"')
                lines.append(f'{prefix}{key}: "{escaped}"')
        return lines

    return "\n".join(_emit(data, 0)) + "\n"


def load_config(path: Path) -> SealimgConfig:
    payload = parse_yaml_object(path.read_text(encoding="utf-8"))
    return SealimgConfig.from_dict(payload)


def save_config(path: Path, config: SealimgConfig) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump_yaml_object(config.to_dict()), encoding="utf-8")
