# Quickstart

## 1) Install (from source)
From repo root:
```bash
python -m venv .venv
source .venv/bin/activate   # Linux/WSL
# .\.venv\Scripts\Activate.ps1   # Windows PowerShell
pip install -U pip
pip install -e ".[dev]"
```

## 2) Create a keypair (one-time)
```bash
sealimg keygen --ed25519 --name "Your Name" \
  --key-name "yourname" \
  --output-dir "~/.sealimg/keys" \
  --passphrase "choose-a-strong-passphrase"
````

* This stores an encrypted private key under `~/.sealimg/keys/`.
* Run `sealimg key show` to print/export your public key.

## 3) Configure defaults (optional)

```bash
sealimg config set --author "Your Name" \
  --site "https://yourdomain.example" \
  --license "CC BY-NC 4.0" \
  --output-root "./sealed" \
  --default-profile "web" \
  --signing-key "~/.sealimg/keys/yourname_ed25519.key"
```

## 4) Seal one image

```bash
sealimg seal path/to/image.jpg --bundle on --passphrase "choose-a-strong-passphrase"
```

Outputs (example):

```
sealed/IMG-2025-10-15-0001/
  source_IMG-2025-10-15-0001_master.jpg
  source_IMG-2025-10-15-0001_web.jpg
  manifest.json
  manifest.sig
  sha256.txt
  README.txt
```

## 5) Verify

```bash
sealimg verify sealed/IMG-2025-10-15-0001/manifest.json \
  --pubkey ~/.sealimg/keys/yourname_ed25519.pub
```

Shows:

* IPTC/XMP summary
* C2PA presence (if embedded)
* SHA-256 matches manifest
* Signature is valid for your public key

## 6) Batch seal a folder

```bash
sealimg seal ./my-portfolio --recursive --profile web \
  --passphrase "choose-a-strong-passphrase"
```

## 7) Launch the desktop GUI (optional)

After install, either command starts the same local GUI:
```bash
sealimg gui
# or
sealimg-gui
```

Pass startup defaults if needed:
```bash
sealimg-gui --config-path ~/.sealimg/config.yml --profile web --output-root ./sealed
```
If no key exists yet, the GUI will offer to generate one and initialize config values first.
You can also click `Setup keys` in the GUI before your first seal run.
Drag-and-drop into the input list uses `tkinterdnd2` when available.
The Profile control is a dropdown, and `Manage...` opens a modal to add/edit/delete profiles.
Watermark controls in the main GUI are read-only and reflect the selected profile settings.
 
## Next Steps

* See `docs/cli.md` for all commands.
* See `docs/manifest.md` for schema.
* See `docs/file-formats.md` for embedding behavior.
* See `docs/integrations/README.md` for WordPress and SmileCMS publishing patterns.
