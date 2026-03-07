# Sealimg

[![CI](https://img.shields.io/github/actions/workflow/status/taggedzi/sealimg/ci.yml?branch=main&label=CI)](https://github.com/taggedzi/sealimg/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/taggedzi/sealimg)](https://github.com/taggedzi/sealimg/releases)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Local-first image provenance sealing for creators.

Sealimg helps you prove authorship and package evidence with every image export:
- signed `manifest.json` + `manifest.sig`
- hash records (`sha256.txt`)
- metadata embedding (XMP/IPTC)
- optional visible + invisible watermarking
- optional embedded provenance marker (C2PA-style best effort)

## Why use it

Images are easy to copy and strip of context. Sealimg makes provenance routine by creating a repeatable package per image with cryptographic signatures and verification tooling. It is designed for solo creators and small teams who want local control (no SaaS dependency).

## Install

### From source (recommended today)

```bash
python -m venv .venv
source .venv/bin/activate   # Windows PowerShell: .\.venv\Scripts\Activate.ps1
pip install -U pip
pip install -e ".[dev]"
```

## Quick start (CLI)

1. Generate signing keys (one-time):

```bash
sealimg keygen --ed25519 --name "Your Name" \
  --key-name "yourname" \
  --output-dir "~/.sealimg/keys" \
  --passphrase "choose-a-strong-passphrase"
```

2. Set defaults:

```bash
sealimg config set --author "Your Name" \
  --site "https://yourdomain.example" \
  --license "CC BY-NC 4.0" \
  --output-root "./sealed" \
  --default-profile "web" \
  --signing-key "~/.sealimg/keys/yourname_ed25519.key"
```

3. Seal an image:

```bash
sealimg seal path/to/image.jpg --bundle on --passphrase "choose-a-strong-passphrase"
```

4. Verify package integrity:

```bash
sealimg verify sealed/IMG-2026-03-07-0001/manifest.json \
  --pubkey ~/.sealimg/keys/yourname_ed25519.pub
```

Example output folder:

```text
sealed/IMG-2026-03-07-0001/
  photo_IMG-2026-03-07-0001_master.jpg
  photo_IMG-2026-03-07-0001_web.jpg
  manifest.json
  manifest.sig
  sha256.txt
  README.txt
  provenance.zip   # optional
```

## GUI usage

Launch either entrypoint:

```bash
sealimg gui
# or
sealimg-gui
```

GUI highlights:
- drag/drop files/folders (when `tkinterdnd2` is available)
- profile selection + profile manager
- settings modal for non-profile config values
- setup-key helper
- about modal with copyable environment diagnostics

## Core commands

- `sealimg seal ...` seal images/folders
- `sealimg watch ...` watch a folder and auto-seal new files
- `sealimg verify ...` verify hashes/signature/key match
- `sealimg inspect ...` inspect metadata/embed status/invisible claim
- `sealimg profile ...` manage profiles
- `sealimg config ...` manage defaults

## Configuration

Default config path: `~/.sealimg/config.yml`

Important keys:
- `author`, `website`, `license`
- `default_profile`, `output_root`, `signing_key`
- `artifact_naming`: `source-id` (default) or `legacy`
- `profiles`: export/watermark behavior

## Trust model notes

- Sidecar manifest signature is the authoritative proof.
- Embedded markers are best-effort and format-dependent.
- Invisible watermarking is a deterrence layer, not a legal guarantee.

## Documentation

- [Quickstart](docs/quickstart.md)
- [CLI reference](docs/cli.md)
- [Config](docs/config.md)
- [Manifest format](docs/manifest.md)
- [File formats and embedding behavior](docs/file-formats.md)
- [FAQ](docs/faq.md)

Legacy planning/spec README content is archived at:
- [docs/archive/readme-spec-2026-03-07.md](docs/archive/readme-spec-2026-03-07.md)

## License

MIT. See [LICENSE](LICENSE).
