"""CLI entrypoint for the Sealimg tool."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Sequence

from . import __version__
from .config import SealimgConfig, dump_yaml_object, load_config, save_config
from .crypto import CryptoError, generate_keypair, public_key_fingerprint
from .image_pipeline import ImagePipelineError
from .metadata import MetadataFields
from .workflow import (
    derive_paths_from_config,
    discover_input_images,
    inspect_image,
    seal_image,
    verify_target,
)

DEFAULT_CONFIG_PATH = Path("~/.sealimg/config.yml").expanduser()


def _default_config() -> SealimgConfig:
    return SealimgConfig.from_dict(
        {
            "author": "Your Name",
            "website": "https://yourdomain.example",
            "license": "CC BY-NC 4.0",
            "default_profile": "web",
            "output_root": "./sealed",
            "signing_key": "~/.sealimg/keys/sealimg_ed25519.key",
            "profiles": {
                "web": {
                    "long_edge": 2560,
                    "jpeg_quality": 82,
                    "wm_visible": {"enabled": True, "text": "", "style": "diag-low"},
                    "wm_invisible": {"enabled": False},
                }
            },
        }
    )


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
    keygen.add_argument("--config-path", default=str(DEFAULT_CONFIG_PATH), help="Config file path")
    keygen.add_argument("--write-config", action="store_true", help="Write signing key to config")

    key = subparsers.add_parser("key", help="Key operations")
    key_sub = key.add_subparsers(dest="key_command", required=True)
    key_show = key_sub.add_parser("show", help="Show key fingerprint and/or public key")
    key_show.add_argument("public_key", help="Path to PEM public key")
    key_show.add_argument("--fingerprint", action="store_true", help="Print fingerprint only")
    key_show.add_argument("--pubkey", action="store_true", help="Print public key only")

    seal = subparsers.add_parser("seal", help="Seal image files")
    seal.add_argument("paths", nargs="+")
    seal.add_argument("--recursive", action="store_true")
    seal.add_argument("--profile", default=None)
    seal.add_argument("--wm-visible", choices=["on", "off"], default=None)
    seal.add_argument("--wm-invisible", choices=["on", "off"], default=None)
    seal.add_argument("--bundle", choices=["on", "off"], default="off")
    seal.add_argument("--no-embed", action="store_true")
    seal.add_argument("--id-prefix", default="IMG")
    seal.add_argument("--author", default=None)
    seal.add_argument("--site", default=None)
    seal.add_argument("--license", dest="license_value", default=None)
    seal.add_argument("--output-root", default=None)
    seal.add_argument("--signing-key", default=None)
    seal.add_argument("--passphrase", default=None)
    seal.add_argument("--config-path", default=str(DEFAULT_CONFIG_PATH))
    seal.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")

    verify = subparsers.add_parser("verify", help="Verify a manifest/image")
    verify.add_argument("target")
    verify.add_argument("--pubkey", default=None)
    verify.add_argument("--config-path", default=str(DEFAULT_CONFIG_PATH))
    verify.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")

    inspect = subparsers.add_parser("inspect", help="Inspect image metadata and embed status")
    inspect.add_argument("image")
    inspect.add_argument("--json", action="store_true", help="Emit machine-readable JSON output")

    config = subparsers.add_parser("config", help="Set/view defaults")
    config_sub = config.add_subparsers(dest="config_command", required=True)
    config_set = config_sub.add_parser("set", help="Set config values")
    config_set.add_argument("--author", default=None)
    config_set.add_argument("--site", default=None)
    config_set.add_argument("--license", dest="license_value", default=None)
    config_set.add_argument("--output-root", default=None)
    config_set.add_argument("--default-profile", default=None)
    config_set.add_argument("--signing-key", default=None)
    config_set.add_argument("--config-path", default=str(DEFAULT_CONFIG_PATH))
    config_get = config_sub.add_parser("get", help="Print config")
    config_get.add_argument("--config-path", default=str(DEFAULT_CONFIG_PATH))

    profile = subparsers.add_parser("profile", help="Manage profiles")
    profile_sub = profile.add_subparsers(dest="profile_command", required=True)
    profile_list = profile_sub.add_parser("list", help="List profiles")
    profile_list.add_argument("--config-path", default=str(DEFAULT_CONFIG_PATH))
    profile_show = profile_sub.add_parser("show", help="Show profile")
    profile_show.add_argument("name")
    profile_show.add_argument("--config-path", default=str(DEFAULT_CONFIG_PATH))
    profile_add = profile_sub.add_parser("add", help="Add or update profile")
    profile_add.add_argument("name")
    profile_add.add_argument("--long-edge", type=int, default=2560)
    profile_add.add_argument("--quality", type=int, default=82)
    profile_add.add_argument("--wm-visible", choices=["on", "off"], default="on")
    profile_add.add_argument("--wm-invisible", choices=["on", "off"], default="off")
    profile_add.add_argument("--wm-style", default="diag-low")
    profile_add.add_argument("--wm-text", default="")
    profile_add.add_argument("--config-path", default=str(DEFAULT_CONFIG_PATH))

    return parser


def _load_or_init_config(config_path: Path) -> SealimgConfig:
    if config_path.exists():
        return load_config(config_path)
    config = _default_config()
    save_config(config_path, config)
    return config


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
        if args.write_config:
            config_path = Path(args.config_path).expanduser()
            cfg = _load_or_init_config(config_path)
            merged = cfg.to_dict()
            merged["signing_key"] = str(info.paths.private_key)
            save_config(config_path, SealimgConfig.from_dict(merged))
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

    if args.command == "config":
        config_path = Path(args.config_path).expanduser()
        cfg = _load_or_init_config(config_path)
        if args.config_command == "get":
            print(dump_yaml_object(cfg.to_dict()), end="")
            return 0
        if args.config_command == "set":
            data = cfg.to_dict()
            if args.author:
                data["author"] = args.author
            if args.site:
                data["website"] = args.site
            if args.license_value:
                data["license"] = args.license_value
            if args.output_root:
                data["output_root"] = args.output_root
            if args.default_profile:
                data["default_profile"] = args.default_profile
            if args.signing_key:
                data["signing_key"] = args.signing_key
            updated = SealimgConfig.from_dict(data)
            save_config(config_path, updated)
            print(f"Config updated: {config_path}")
            return 0

    if args.command == "profile":
        config_path = Path(args.config_path).expanduser()
        cfg = _load_or_init_config(config_path)
        if args.profile_command == "list":
            for name in sorted(cfg.profiles):
                print(name)
            return 0
        if args.profile_command == "show":
            if args.name not in cfg.profiles:
                print(f"Error: profile '{args.name}' not found.")
                return 1
            print(dump_yaml_object(cfg.profiles[args.name]), end="")
            return 0
        if args.profile_command == "add":
            data = cfg.to_dict()
            data["profiles"][args.name] = {
                "long_edge": args.long_edge,
                "jpeg_quality": args.quality,
                "wm_visible": {
                    "enabled": args.wm_visible == "on",
                    "style": args.wm_style,
                    "text": args.wm_text,
                },
                "wm_invisible": {"enabled": args.wm_invisible == "on"},
            }
            updated = SealimgConfig.from_dict(data)
            save_config(config_path, updated)
            print(f"Profile '{args.name}' saved.")
            return 0

    if args.command == "seal":
        config_path = Path(args.config_path).expanduser()
        cfg = _load_or_init_config(config_path)
        passphrase = args.passphrase or os.environ.get("SEALIMG_PASSPHRASE")
        if not passphrase:
            print("Error: passphrase required (--passphrase or SEALIMG_PASSPHRASE).")
            return 1
        try:
            signing_key, public_key = derive_paths_from_config(
                cfg,
                signing_key_override=args.signing_key,
            )
        except FileNotFoundError as exc:
            print(f"Error: {exc}")
            return 1

        output_root = Path(args.output_root or cfg.output_root).expanduser()
        profile_name = args.profile or cfg.default_profile
        selected_profile = cfg.profiles.get(profile_name)
        if selected_profile is None:
            print(f"Error: profile '{profile_name}' not found.")
            return 1
        overrides = {}
        if args.wm_visible:
            overrides.setdefault("wm_visible", {})["enabled"] = args.wm_visible == "on"
        if args.wm_invisible:
            overrides.setdefault("wm_invisible", {})["enabled"] = args.wm_invisible == "on"

        metadata = MetadataFields(
            author=args.author or cfg.author,
            website=args.site or cfg.website,
            license=args.license_value or cfg.license,
            copyright_notice=f"(c) {args.author or cfg.author}",
        )
        inputs = discover_input_images([Path(p) for p in args.paths], recursive=args.recursive)
        if not inputs:
            print("Error: no supported input images found.")
            return 1

        from .ids import ImageIdGenerator

        id_gen = ImageIdGenerator(prefix=args.id_prefix)
        exit_code = 0
        json_results = []
        for image in inputs:
            try:
                result = seal_image(
                    input_path=image,
                    output_root=output_root,
                    id_generator=id_gen,
                    metadata=metadata,
                    profile_defaults=cfg.profiles.get("web", {}),
                    selected_profile=selected_profile,
                    cli_overrides=overrides,
                    bundle=args.bundle == "on",
                    embed_enabled=not args.no_embed,
                    signing_key_path=signing_key,
                    passphrase=passphrase,
                    signer_name=metadata.author,
                    public_key_path=public_key,
                )
                json_results.append(
                    {
                        "input": str(image),
                        "image_id": result.image_id,
                        "output_dir": str(result.output_dir),
                        "master": str(result.master_path),
                        "web": str(result.web_path),
                        "manifest": str(result.manifest_path),
                        "signature": str(result.signature_path),
                        "sha256": str(result.sha_path),
                        "readme": str(result.readme_path),
                        "bundle": str(result.zip_path) if result.zip_path else None,
                        "embed_status": result.embed_status.status,
                        "embed_message": result.embed_status.message,
                    }
                )
                if not args.json:
                    print(f"Sealed {image} -> {result.output_dir}")
                    print(
                        f"Embed status: {result.embed_status.status} "
                        f"({result.embed_status.message})"
                    )
            except ImagePipelineError as exc:
                if not args.json:
                    print(f"Error: unsupported or invalid image '{image}': {exc}")
                exit_code = 3
            except Exception as exc:
                if not args.json:
                    print(f"Error sealing '{image}': {exc}")
                exit_code = 1
        if args.json:
            print(
                json.dumps(
                    {
                        "ok": exit_code == 0,
                        "exit_code": exit_code,
                        "count": len(json_results),
                        "results": json_results,
                    },
                    sort_keys=True,
                )
            )
        return exit_code

    if args.command == "verify":
        pubkey = Path(args.pubkey).expanduser() if args.pubkey else None
        if pubkey is None:
            config_path = Path(args.config_path).expanduser()
            cfg = _load_or_init_config(config_path)
            key = Path(cfg.signing_key).expanduser()
            pubkey = key.with_suffix(".pub")
        if not pubkey.exists():
            print("Error: public key not found. Provide --pubkey or configure signing_key.")
            return 1
        try:
            result = verify_target(Path(args.target), pubkey)
        except FileNotFoundError as exc:
            print(f"Error: {exc}")
            return 1
        except Exception as exc:
            print(f"Error: {exc}")
            return 1

        exit_code = 0
        if not result.signature_valid or not result.hash_valid:
            exit_code = 2
        if args.json:
            print(
                json.dumps(
                    {
                        "ok": exit_code == 0,
                        "exit_code": exit_code,
                        "manifest": str(result.manifest_path),
                        "signature_valid": result.signature_valid,
                        "hash_valid": result.hash_valid,
                        "embed_status": result.embed_status.status,
                        "embed_message": result.embed_status.message,
                    },
                    sort_keys=True,
                )
            )
            return exit_code

        print(f"Manifest: {result.manifest_path}")
        print(f"Signature: {'valid' if result.signature_valid else 'invalid'}")
        print(f"Hashes: {'valid' if result.hash_valid else 'invalid'}")
        print(f"Embed markers: {result.embed_status.status}")
        if not result.signature_valid or not result.hash_valid:
            return 2
        return 0

    if args.command == "inspect":
        try:
            result = inspect_image(Path(args.image))
        except ImagePipelineError as exc:
            print(f"Error: {exc}")
            return 3
        except Exception as exc:
            print(f"Error: {exc}")
            return 1
        if args.json:
            print(
                json.dumps(
                    {
                        "ok": True,
                        "path": str(result.path),
                        "format": result.format,
                        "width": result.width,
                        "height": result.height,
                        "xmp": result.has_xmp,
                        "embed_status": result.embed_status.status,
                        "embed_message": result.embed_status.message,
                    },
                    sort_keys=True,
                )
            )
            return 0
        print(f"Path: {result.path}")
        print(f"Format: {result.format}")
        print(f"Size: {result.width}x{result.height}")
        print(f"XMP: {'present' if result.has_xmp else 'absent'}")
        print(f"Embed markers: {result.embed_status.status} ({result.embed_status.message})")
        return 0

    print(f"Command '{args.command}' is not implemented.")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
