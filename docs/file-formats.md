# File Formats & Embedding

## Supported (initial)
- **PNG/JPEG**: write IPTC/XMP; embed C2PA claim where possible; keep `manifest.json` + `manifest.sig` alongside.
- **AVIF/HEIC/JPEG XL** (later): embed via ISOBMFF boxes/JUMBF.

## Embedding Strategy
1. **Always** produce the external `manifest.json` + `manifest.sig`.
2. **Attempt** to embed a C2PA claim/digest:
   - PNG: ancillary `iTXt` chunk marker (best-effort).
   - JPEG: APP11 marker block with JUMBF-style prefix (best-effort).
   - AVIF/HEIC: ISOBMFF boxes.
3. If embedding is not supported by the host OS/libs, fall back to sidecar-only.

## Current Compatibility Matrix (v0.1 implementation)
| Format | Sidecar (`manifest.json` + `manifest.sig`) | Embedded Marker |
|---|---|---|
| PNG | Yes | Yes (best-effort `iTXt` marker) |
| JPEG | Yes | Yes (best-effort APP11 marker) |
| AVIF/HEIC | No (not yet implemented) | No (not yet implemented) |
| JPEG XL | No (not yet implemented) | No (not yet implemented) |

## Metadata (IPTC/XMP)
- Author, Website, License, Copyright Notice
- Caution: many platforms strip metadata; hence signed manifest exists separately.

## Watermarks
- **Visible**: raster overlay during web export.
- **Invisible**: robust-but-not-perfect; optional deterrence layer.

## Provenance Bundle
- Optional ZIP containing: master, web, manifest.json, manifest.sig, sha256.txt, README.txt.
