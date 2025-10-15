# C2PA Notes (Developer-Facing)

## Goals
- Embed a claim that binds the image to an assertion set (authorship, creation time, tool chain).
- Allow third-party verifiers to display provenance.

## Approach
- Always produce external `manifest.json` + `manifest.sig` (canonical).
- Attempt to embed a C2PA claim referencing/including the manifest using available libraries:
  - JPEG: JUMBF in APP11.
  - PNG: dedicated ancillary chunk (library-dependent).
  - AVIF/HEIC: ISOBMFF boxes.

## Fallback
- If embedding fails, continue with sidecar manifest; verification remains possible.

## Display
- Sealimg will not implement a badge UI itself; it exposes machine-readable results for CMS/plugins to render a badge.
