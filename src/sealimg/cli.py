"""CLI entrypoint for the Sealimg tool."""

from __future__ import annotations

import argparse
from typing import Sequence

from . import __version__


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sealimg",
        description="Seal images with provenance metadata and signatures.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", required=False)

    for name in ("seal", "verify", "inspect", "keygen", "config", "profile"):
        subparsers.add_parser(name, help=f"{name} command (scaffold)")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    print(f"Command '{args.command}' is scaffolded but not implemented yet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
