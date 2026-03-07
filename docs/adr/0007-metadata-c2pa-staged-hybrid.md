# 0007 - Metadata/C2PA Strategy: Staged Hybrid Implementation

- Status: Accepted
- Date: 2026-03-06

## Context
Sealimg needs immediate local-first provenance coverage while preserving a path to stricter standards-compliant C2PA implementations.

## Decision
Use a staged hybrid strategy:
- v0.1: sidecar-first + best-effort PNG/JPEG embedding markers in the local pipeline.
- v0.3+: keep adapter boundary to support stricter C2PA backend integration.

## Consequences
- Users get immediate practical provenance behavior.
- Architecture remains extensible for standards-grade C2PA implementations later.
- Current embedding is intentionally best-effort, not full interoperability parity.

## Alternatives Considered
- Manual embed only forever: simplest, but caps standards compatibility.
- Strict C2PA backend immediately: strongest interoperability, but slower delivery and higher dependency complexity.
