# 0002 - Crypto Strategy: Native Libraries + Optional GPG Interop

- Status: Accepted
- Date: 2026-03-06

## Context
Sealimg requires robust signing and verification for provenance manifests while supporting users who already maintain GPG keys.

## Decision
Use native cryptographic libraries for core key generation/sign/verify features. Also support optional GPG key import/use when a user provides valid GPG material.

## Consequences
- Core behavior is consistent and not hard-coupled to external GPG tooling.
- Existing user trust chains and key workflows can be reused when desired.
- Integration complexity increases due to dual-path key handling and verification UX.

## Alternatives Considered
- Native libs only: simpler implementation, but excludes existing GPG workflows.
- GPG only: broad compatibility for some users, but introduces external dependency and weaker portability guarantees.
