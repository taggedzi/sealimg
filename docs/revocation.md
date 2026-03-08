# Key Revocation Guide

## Why this exists

A valid signature only proves that a specific key signed a manifest.
It does not prove that key is still trustworthy today.

If a private key is leaked, stolen, or retired, creators need a way to mark that key as untrusted for future verification decisions. That is what revocation does.

## What problem this solves

Without revocation:
- a compromised key can continue producing signatures that look cryptographically valid
- verifiers cannot distinguish "valid and trusted" from "valid but compromised"

With revocation:
- verifiers can detect that a signer key has been revoked
- teams can enforce policy (for example, fail verification when key is revoked)
- creators can rotate keys without silent trust drift

## Core concepts

- `fingerprint`: short key identifier (Sealimg uses the first 16 hex chars of SHA-256 of the public key bytes)
- `revocations_file`: text file containing revoked key records
- `strict revocation`: verify mode that returns non-zero when the signer key is revoked

Revocation record format:

```text
<fingerprint> <YYYY-MM-DD> <reason...>
```

Example:

```text
4d2a6b9f1e23ab77 2026-03-08 key compromise
```

## Configure revocation path

Set a project/user default:

```bash
sealimg config set --revocations-file "~/.sealimg/revocations.txt"
```

Config key:
- `revocations_file` in `~/.sealimg/config.yml`

## CLI usage

Add/update a revoked key entry:

```bash
sealimg key revoke \
  --fingerprint 4d2a6b9f1e23ab77 \
  --reason "key compromise" \
  --date 2026-03-08
```

List current revocations:

```bash
sealimg key revocations list
```

Verify with revocation awareness:

```bash
sealimg verify sealed/IMG-2026-03-07-0001/manifest.json \
  --pubkey ~/.sealimg/keys/creator_ed25519.pub
```

Fail verification when key is revoked:

```bash
sealimg verify sealed/IMG-2026-03-07-0001/manifest.json \
  --pubkey ~/.sealimg/keys/creator_ed25519.pub \
  --strict-revocation
```

Use a non-default revocation file for a run:

```bash
sealimg verify ... --revocations-file ./policy/revocations.txt
```

JSON output includes:
- `revocation.key_revoked`
- `revocation.revoked_on`
- `revocation.reason`
- `revocation.revocations_file`

## GUI usage

- `Settings...` now includes `Revocations file`.
- Main window shows read-only:
  - current signing key fingerprint
  - revocation status
- `About...` includes revocation file path for support/debug sharing.

## Recommended operating practice

1. Keep revocation file in version-controlled policy storage or backed-up secure location.
2. Revoke immediately on suspected key compromise.
3. Rotate to a new signing key after revocation.
4. Use `--strict-revocation` in CI/compliance-sensitive verification.

## Important limitation

Revocation status is only as strong as distribution/availability of your revocation file. If a verifier never sees updated revocations, they cannot apply revocation policy.
