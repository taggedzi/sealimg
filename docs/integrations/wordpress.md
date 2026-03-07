# WordPress Integration Guide

This guide shows how to publish Sealimg outputs in a WordPress workflow while preserving provenance context.

## Goals
- publish web-ready images (`web.jpg`)
- keep provenance materials accessible (`manifest.json`, `manifest.sig`, `sha256.txt`)
- display a clear provenance link or badge on post pages

## Recommended Asset Layout

For each sealed output directory:

```text
sealed/IMG-YYYY-MM-DD-####
  web.jpg
  master.jpg|master.png|master.avif|master.heic|master.jxl
  manifest.json
  manifest.sig
  sha256.txt
  README.txt
```

Publish at least:
- `web.jpg`
- `manifest.json`
- `manifest.sig`

Optionally publish:
- `sha256.txt`
- `README.txt`

## Basic Publishing Flow

1. Upload `web.jpg` to the Media Library.
2. Upload `manifest.json` and `manifest.sig` to a stable public location.
3. Add a provenance block in the post content:
   - "Provenance manifest"
   - link to `manifest.json`
   - optional link to your public key
4. In the image caption or nearby text, include the image ID from the manifest.

## Suggested Provenance Block

```html
<aside class="sealimg-provenance">
  <strong>Provenance:</strong>
  <a href="https://example.com/provenance/IMG-2026-03-07-0001/manifest.json">manifest.json</a>
  ·
  <a href="https://example.com/provenance/IMG-2026-03-07-0001/manifest.sig">manifest.sig</a>
  ·
  <a href="https://example.com/keys/creator_ed25519.pub">public key</a>
</aside>
```

## Verification Pattern

For high-value pages, run verification in CI before deploy:

```bash
sealimg verify ./provenance/IMG-2026-03-07-0001/manifest.json --pubkey ./keys/creator_ed25519.pub
```

Fail deployment if exit code is non-zero.

## Notes
- WordPress image optimization plugins can alter uploaded image files. Prefer verifying against published sidecar package, not post-processed CDN variants.
- Treat sidecar files as canonical evidence even when embedded markers are absent.
