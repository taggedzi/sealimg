"""Optional GPG interop helpers."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path


class GpgError(RuntimeError):
    """Raised when GPG operations fail."""


def has_gpg() -> bool:
    return shutil.which("gpg") is not None


def _run_gpg(args: list[str], homedir: Path | None = None) -> subprocess.CompletedProcess[str]:
    if not has_gpg():
        raise GpgError("gpg is not installed or not on PATH")

    cmd = ["gpg", "--batch", "--yes"]
    if homedir is not None:
        cmd.extend(["--homedir", str(homedir)])
    cmd.extend(args)

    result = subprocess.run(cmd, text=True, capture_output=True, check=False)
    if result.returncode != 0:
        raise GpgError(result.stderr.strip() or "gpg command failed")
    return result


def import_key(key_path: Path, homedir: Path | None = None) -> None:
    _run_gpg(["--import", str(key_path)], homedir=homedir)


def detached_sign(
    input_path: Path,
    signature_path: Path,
    key_fingerprint: str | None = None,
    homedir: Path | None = None,
    armor: bool = False,
) -> None:
    args = ["--detach-sign", "--output", str(signature_path)]
    if armor:
        args.append("--armor")
    if key_fingerprint:
        args.extend(["--local-user", key_fingerprint])
    args.append(str(input_path))
    _run_gpg(args, homedir=homedir)


def verify_detached(input_path: Path, signature_path: Path, homedir: Path | None = None) -> bool:
    try:
        _run_gpg(["--verify", str(signature_path), str(input_path)], homedir=homedir)
        return True
    except GpgError:
        return False
