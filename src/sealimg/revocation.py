"""Key revocation list parsing and lookup."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


@dataclass(frozen=True)
class RevokedKey:
    fingerprint: str
    revoked_on: str
    reason: str


def parse_revocation_lines(lines: Iterable[str]) -> list[RevokedKey]:
    entries: list[RevokedKey] = []
    for raw in lines:
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(None, 2)
        if len(parts) < 2:
            continue
        fingerprint = parts[0]
        revoked_on = parts[1]
        reason = parts[2] if len(parts) == 3 else ""
        entries.append(RevokedKey(fingerprint=fingerprint, revoked_on=revoked_on, reason=reason))
    return entries


def load_revocations(path: Path) -> list[RevokedKey]:
    if not path.exists():
        return []
    return parse_revocation_lines(path.read_text(encoding="utf-8").splitlines())


def find_revoked(fingerprint: str, revocations: list[RevokedKey]) -> RevokedKey | None:
    for entry in revocations:
        if entry.fingerprint == fingerprint:
            return entry
    return None
