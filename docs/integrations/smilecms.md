# SmileCMS Integration Guide

This guide outlines a sidecar-first ingestion model for SmileCMS.

## Goals
- ingest sealed image packages consistently
- expose provenance links in content rendering
- preserve verification paths for downstream consumers

## Ingestion Contract

For each asset, ingest:
- display image: `web.jpg`
- provenance manifest: `manifest.json`
- detached signature: `manifest.sig`
- optional support files: `sha256.txt`, `README.txt`

Required metadata fields to index from `manifest.json`:
- `image_id`
- `author`
- `website`
- `license`
- `signature.signer_key_id`
- `timestamps.sealed_utc`
- `timestamps.public_proof` (when present)

## Suggested SmileCMS Model Fields

- `image_url`
- `manifest_url`
- `signature_url`
- `image_id`
- `author_name`
- `license_name`
- `signer_key_id`
- `sealed_utc`
- `public_proof`

## Rendering Pattern

On content pages:
1. Render image normally.
2. Show a "Provenance" badge next to or below image.
3. Badge links to `manifest.json`.
4. Optionally provide "Verify" action linking to docs/tooling.

## Verification Hook (Recommended)

Add an ingestion validation step:
- fetch uploaded `manifest.json` and `manifest.sig`
- run `sealimg verify` against provided public key
- reject or quarantine failed assets

Example:

```bash
sealimg verify /ingest/IMG-2026-03-07-0001/manifest.json --pubkey /keys/creator_ed25519.pub
```

## Operational Notes
- Sidecar files should be immutable once published.
- If SmileCMS generates derived images, keep provenance links tied to the canonical sealed package.
- Store manifest and signature URLs in durable object storage paths to avoid link rot.
