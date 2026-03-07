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

## Trust & Sharing Guidance
- Share only your public key (`*.pub`) with verifiers.
- Publish your public key fingerprint in a stable place you control (website/profile/bio).
- Keep the private key encrypted and offline-backed up; never share it.
- If compromise is suspected, rotate keys and publish revocation details immediately.
- Past signatures remain verifiable if verifiers retain the old public key and revocation timeline.

## Verification
- Anyone can verify `manifest.json` with your public key.
- `sealimg verify` also compares file SHA-256 values against the manifest and checks any embedded C2PA structures.
