"""Image ID generation utilities."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date

ID_RE = re.compile(r"^(?P<prefix>[A-Z0-9_-]+)-(?P<day>\d{4}-\d{2}-\d{2})-(?P<seq>\d{4})$")


@dataclass
class ImageIdGenerator:
    prefix: str = "IMG"
    _counters: dict[str, int] = field(default_factory=dict)

    def next_id(self, day: date | None = None, existing_ids: set[str] | None = None) -> str:
        target = day or date.today()
        day_key = target.strftime("%Y-%m-%d")
        existing_max = _max_existing_seq(self.prefix, day_key, existing_ids or set())
        current = self._counters.get(day_key, existing_max)
        seq = current + 1
        self._counters[day_key] = seq
        return f"{self.prefix}-{day_key}-{seq:04d}"


def _max_existing_seq(prefix: str, day: str, existing_ids: set[str]) -> int:
    max_seq = 0
    for image_id in existing_ids:
        match = ID_RE.match(image_id)
        if not match:
            continue
        if match.group("prefix") != prefix or match.group("day") != day:
            continue
        max_seq = max(max_seq, int(match.group("seq")))
    return max_seq
