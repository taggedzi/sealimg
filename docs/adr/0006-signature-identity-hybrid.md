# 0006 - Signature Identity: Hybrid Display Name + Key-Bound ID

- Status: Accepted
- Date: 2026-03-06

## Context
Sealimg must remain usable for creators while providing an auditable identity anchor during verification.

## Decision
Adopt a hybrid signature identity model:
- `signature.signer_display`: user-friendly display name.
- `signature.signer_key_id`: authoritative key-bound ID (fingerprint).

For compatibility during transition, `signature.signer` and `signature.pubkey_fingerprint` remain supported.

## Consequences
- Verification can enforce key-ID matching, reducing identity ambiguity.
- UX remains creator-friendly with display names.
- Schema and docs become slightly more complex, but trust semantics improve.

## Alternatives Considered
- Free-text only (`signer`): simple UX, weaker identity binding.
- Key-bound only: stronger trust, weaker ergonomics for non-technical users.
