# File Formats & Embedding

## Supported (initial)
- **PNG/JPEG**: write IPTC/XMP; embed C2PA claim where possible; keep `manifest.json` + `manifest.sig` alongside.
- **AVIF/HEIC/JPEG XL** (later): embed via ISOBMFF boxes/JUMBF.

## Embedding Strategy
1. **Always** produce the external `manifest.json` + `manifest.sig`.
2. **Attempt** to embed a C2PA claim/digest:
   - PNG: ancillary chunk (via library support).
   - JPEG: JUMBF box (APP11).
   - AVIF/HEIC: ISOBMFF boxes.
3. If embedding is not supported by the host OS/libs, fall back to sidecar-only.

## Metadata (IPTC/XMP)
- Author, Website, License, Copyright Notice
- Caution: many platforms strip metadata; hence signed manifest exists separately.

## Watermarks
- **Visible**: raster overlay during web export.
- **Invisible**: robust-but-not-perfect; optional deterrence layer.

## Provenance Bundle
- Optional ZIP containing: master, web, manifest.json, manifest.sig, sha256.txt, README.txt.
