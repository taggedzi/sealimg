# Sealimg — Overview

Sealimg is a tiny, local-first tool that “seals” images with provenance so creators can share freely and sleep at night. It adds clear authorship and licensing info, embeds a signed provenance manifest (C2PA-compatible where supported), writes human-readable IPTC/XMP metadata, and can export a ready-to-publish web copy. No cloud account, no subscription, no vendor lock-in.

## What Sealimg Is (v1)
- **Local** sealing: runs offline by default.
- **Open** formats: PNG/JPEG first; AVIF/HEIC/JPEG XL later.
- **Human-readable** manifest (JSON) + **cryptographic signature**.
- **C2PA embedding** where filetypes support it (via JUMBF/boxes).
- Optional: **visible** and **invisible** watermarks.
- Optional: **provenance bundle** (ZIP) for power users/archive.

## Non-Goals
- Not a CMS or DAM.
- Not a legal service.
- No tracking, no analytics, no phoning home.

## Trust Model
- Your machine is trusted; keys are stored locally, encrypted.
- Public verification does **not** require trusting Sealimg: anyone can verify signatures with your public key and independent tools.

## Typical Flow
1. Drop images into a folder.
2. Run `sealimg seal <folder>`.
3. Get:
   - Master copy (lossless, embedded metadata/manifest).
   - Web copy (resized, visible watermark if enabled).
   - `manifest.json` + `manifest.sig`.
   - `sha256.txt`, `README.txt`.
   - Optional `provenance.zip`.

## Key Terms
- **C2PA**: Open standard for content provenance manifests.
- **JUMBF**: Container to embed structured data inside images.
- **IPTC/XMP**: Common metadata fields (author, copyright, URL).
- **SHA-256**: Cryptographic file fingerprint.
- **Ed25519/RSA**: Signature algorithms.
