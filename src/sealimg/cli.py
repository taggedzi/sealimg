"""CLI entrypoint for the Sealimg tool."""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from typing import Sequence

from . import __version__
from .crypto import CryptoError, generate_keypair, public_key_fingerprint


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sealimg",
        description="Seal images with provenance metadata and signatures.",
    )
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")

    subparsers = parser.add_subparsers(dest="command", required=False)

    keygen = subparsers.add_parser("keygen", help="Generate encrypted signing keys")
    algo = keygen.add_mutually_exclusive_group(required=False)
    algo.add_argument("--ed25519", action="store_true", help="Generate Ed25519 key pair (default)")
    algo.add_argument("--rsa", action="store_true", help="Generate RSA key pair")
    keygen.add_argument("--name", default="sealimg", help="Signer/display name")
    keygen.add_argument("--key-name", default="sealimg", help="Base key filename")
    keygen.add_argument("--output-dir", default=".sealimg/keys", help="Directory for key files")
    keygen.add_argument(
        "--passphrase",
        default=None,
        help="Private key passphrase (defaults to SEALIMG_PASSPHRASE env var)",
    )

    key = subparsers.add_parser("key", help="Key operations")
    key_sub = key.add_subparsers(dest="key_command", required=True)
    key_show = key_sub.add_parser("show", help="Show key fingerprint and/or public key")
    key_show.add_argument("public_key", help="Path to PEM public key")
    key_show.add_argument("--fingerprint", action="store_true", help="Print fingerprint only")
    key_show.add_argument("--pubkey", action="store_true", help="Print public key only")

    for name in ("seal", "verify", "inspect", "config", "profile"):
        subparsers.add_parser(name, help=f"{name} command (scaffold)")

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.command:
        parser.print_help()
        return 0

    if args.command == "keygen":
        passphrase = args.passphrase or os.environ.get("SEALIMG_PASSPHRASE")
        if not passphrase:
            print("Error: passphrase required (--passphrase or SEALIMG_PASSPHRASE).")
            return 1
        algorithm = "rsa" if args.rsa else "ed25519"
        try:
            info = generate_keypair(
                output_dir=Path(args.output_dir),
                signer=args.name,
                passphrase=passphrase,
                algorithm=algorithm,
                key_name=args.key_name,
            )
        except CryptoError as exc:
            print(f"Error: {exc}")
            return 1
        print(f"Generated {info.algorithm} keys for '{info.signer}'.")
        print(f"Private key: {info.paths.private_key}")
        print(f"Public key: {info.paths.public_key}")
        print(f"Fingerprint: {info.fingerprint}")
        return 0

    if args.command == "key":
        if args.key_command == "show":
            try:
                key_bytes = Path(args.public_key).read_bytes()
            except OSError as exc:
                print(f"Error: unable to read key file: {exc}")
                return 1
            fingerprint = public_key_fingerprint(key_bytes)
            show_all = not args.fingerprint and not args.pubkey
            if args.fingerprint or show_all:
                print(fingerprint)
            if args.pubkey or show_all:
                try:
                    print(key_bytes.decode("utf-8"))
                except UnicodeDecodeError:
                    print("Error: public key is not valid UTF-8 PEM text.")
                    return 1
            return 0

    print(f"Command '{args.command}' is scaffolded but not implemented yet.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
