# Manifest Schema (v1)

Each sealed image has a human-readable `manifest.json` that is also signed (`manifest.sig`). Where supported, a C2PA claim referencing the manifest is embedded into the image (JUMBF/box).

## Minimal Fields
```json
{
  "schema": "https://sealimg.org/provenance/v1",
  "image_id": "IMG-YYYY-MM-DD-####",
  "author": "Your Name",
  "website": "https://yourdomain.example",
  "license": "CC BY-NC 4.0",
  "files": {
    "master": {"path": "master.png", "sha256": "<hex>"},
    "web": {"path": "web.jpg", "sha256": "<hex>"}
  },
  "timestamps": {
    "local_created": "2025-10-15T03:12:05-04:00",
    "sealed_utc": "2025-10-15T07:12:20Z"
  },
  "signature": {
    "algo": "ed25519|rsa",
    "signer": "Your Name",
    "pubkey_fingerprint": "<short>",
    "signature_file": "manifest.sig"
  }
}
````

## Optional Fields

* `title`, `notes`
* `source`: `{ ai_assisted, ai_base, edited_by_human, tools[] }`
* `watermarks`: `{ visible: {...}, invisible: {...} }`
* `timestamps.public_proof`: URL or reference where the manifest hash is published.
* `links`: prior publication URLs (e.g., DeviantArt).

## Design Principles

* **Human-friendly**: easy to read in any text editor.
* **Stable**: additive changes should not break old manifests.
* **Decoupled**: verification doesn’t require Sealimg (standard crypto).
