# Quickstart

## 1) Install (placeholder)
> Installation steps will be added once the first CLI is published.
- Windows/macOS/Linux binaries or `pip`/`cargo` install TBD.

## 2) Create a keypair (one-time)
```bash
sealimg keygen --ed25519 --name "Your Name"
````

* This stores an encrypted private key under `~/.sealimg/keys/`.
* Run `sealimg key show` to print/export your public key.

## 3) Configure defaults (optional)

```bash
sealimg config set --author "Your Name" \
  --site "https://yourdomain.example" \
  --license "CC BY-NC 4.0" \
  --output-root "./sealed" \
  --default-profile "web"
```

## 4) Seal one image

```bash
sealimg seal path/to/image.jpg
```

Outputs (example):

```
sealed/IMG-2025-10-15-0001/
  master.jpg
  web.jpg
  manifest.json
  manifest.sig
  sha256.txt
  README.txt
```

## 5) Verify

```bash
sealimg verify sealed/IMG-2025-10-15-0001/web.jpg
```

Shows:

* IPTC/XMP summary
* C2PA presence (if embedded)
* SHA-256 matches manifest
* Signature is valid for your public key

## 6) Batch seal a folder

```bash
sealimg seal ./my-portfolio --recursive --profile web
```

## Next Steps

* See `docs/cli.md` for all commands.
* See `docs/manifest.md` for schema.
* See `docs/file-formats.md` for embedding behavior.
