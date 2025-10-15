# UX Flows (Draft)

## CLI Primary Flow
1) User runs `sealimg seal <input>`.
2) If no key, prompt to create one.
3) Assign image_id, write IPTC/XMP.
4) Create master copy; compute SHA-256.
5) Create web copy; apply visible watermark if enabled.
6) Build `manifest.json`; sign -> `manifest.sig`.
7) Attempt C2PA embed; fall back to sidecar.
8) Emit `README.txt` and optional `provenance.zip`.
9) Print a friendly table of outputs.

## GUI Primary Flow (later)
- Drag files → Sealed Cards appear with:
  - Thumbnail, image_id
  - Status: metadata ✔, signature ✔, C2PA ✔/sidecar
  - Buttons: Show manifest, Copy hashes, Open folder
