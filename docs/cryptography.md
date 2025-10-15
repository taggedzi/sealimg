# Cryptography

## Hashes
- **SHA-256** for all files (master/web/manifest).

## Signatures
- Default: **Ed25519** (fast, modern).
- Alternative: **RSA-2048+** (compatibility).
- `manifest.json` is the canonical signed object.
- Output: detached signature `manifest.sig`.

## Keys
- Private key stored locally, encrypted with passphrase.
- Public key exportable for verifiers.
- Keep an offline backup + revocation file.

## Verification
- Anyone can verify `manifest.json` with your public key.
- `sealimg verify` also compares file SHA-256 values against the manifest and checks any embedded C2PA structures.
