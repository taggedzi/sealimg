# 0003 - Master Output Policy: Pixel-Preserving with Metadata Allowed

- Status: Accepted
- Date: 2026-03-06

## Context
Sealimg outputs a `master` artifact intended to preserve source image fidelity while carrying provenance and metadata.

## Decision
Define `master` as pixel-preserving, not byte-identical. Metadata/provenance updates are allowed on the master output.

## Consequences
- IPTC/XMP/C2PA data can be embedded directly in master outputs.
- Manifest and inspect workflows become more self-contained.
- Documentation and UX must avoid claiming master files are exact byte-for-byte originals.

## Alternatives Considered
- Byte-identical master: stronger archival identity claim, but cannot carry embedded metadata/provenance without extra artifact duplication.
