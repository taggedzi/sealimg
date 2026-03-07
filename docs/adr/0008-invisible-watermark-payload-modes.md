# 0008 - Invisible Watermark Payload Modes

- Status: Accepted
- Date: 2026-03-07

## Context
Sealimg needs invisible watermark behavior for multiple distribution scenarios:
- public sharing with durable ownership attribution,
- client-specific deliveries with recipient tracing,
- neutral provenance linking without identity-specific data.

Using one fixed payload strategy for all cases creates privacy and workflow tradeoffs.

## Decision
Adopt explicit invisible payload modes:
- `auto` (default): recipient fingerprint when recipient ID is provided; otherwise image ID.
- `image-id`: always image ID.
- `recipient`: recipient fingerprint only; requires recipient ID.
- `owner`: owner fingerprint derived from `author`, `website`, and signer key ID.

Manifest records include:
- `watermarks.invisible.mode`
- `watermarks.invisible.payload`
- optional `recipient_fingerprint` and `owner_fingerprint` when applicable.

## Consequences
- Users can select privacy vs traceability behavior intentionally.
- Public releases can embed ownership attribution without recipient data.
- Recipient mode prevents accidental fallback by requiring recipient ID.
- Manifest and CLI/GUI behavior are slightly more complex but clearer.

## Alternatives Considered
- Always embed all identifiers: rejected for privacy/correlation risk and payload bloat.
- Keep single implicit behavior: rejected for lack of control across distribution contexts.
