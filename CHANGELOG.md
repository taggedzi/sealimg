# Changelog
All notable changes to this project will be documented in this file.

The format is based on **Keep a Changelog** and this project adheres to **Semantic Versioning**.

## [Unreleased]
### Added
- N/A

### Changed
- N/A

### Fixed
- N/A

---

## [1.0.0] - 2026-03-07
### Added
- Local desktop GUI (`sealimg gui` and `sealimg-gui`) for sealing workflows.
- First-run GUI setup flow to bootstrap signing keys and initialize config.
- Explicit GUI `Setup keys` action and drag-and-drop input support.
- `tkinterdnd2` integration for cross-platform drag-and-drop behavior.
- Integration guides for WordPress and SmileCMS publishing workflows.
- Sidecar-first expanded format handling across AVIF/HEIC/HEIF/JXL flows.
- Recipient fingerprint and pHash output in sealing and verification outputs.
- Third-party notices file for bundled/runtime dependencies.

### Changed
- CI matrix optimized for resource usage: Windows runs on Python 3.13; Linux keeps 3.11/3.12/3.13.
- CLI and quickstart docs aligned with GUI onboarding and drag-and-drop behavior.

### Fixed
- Branch-protection check mismatch from removed Windows matrix jobs resolved via required-check updates.
- CRLF normalization workflow clarified and stabilized for cross-platform contribution flow.

---

## [0.1.0-rc1] - 2026-03-07
### Added
- Python package scaffold, CLI entrypoint, and Windows/Linux CI workflow.
- Config and manifest domain models with validation and profile merge logic.
- Native crypto key generation/sign/verify (Ed25519 + RSA) with optional GPG interop helpers.
- PNG/JPEG pipeline for master/web outputs with XMP metadata embedding.
- Artifact pipeline for `manifest.json`, `manifest.sig`, `sha256.txt`, `README.txt`, and provenance ZIP.
- Sidecar-first C2PA embed flow with best-effort JPEG/PNG embedding and inspect detection.
- CLI commands for `seal`, `watch`, `verify`, `inspect`, `keygen`, `key show`, `config`, and `profile`.
- JSON output mode for `seal`, `watch`, `verify`, and `inspect`.
- Timestamp helper support (`--timestamp-log`, `--timestamp-post-url`).
- Golden fixture regression suite (source hashes + manifest snapshot) with real-image fixtures.

### Changed
- `docs/cli.md`, `docs/quickstart.md`, `docs/file-formats.md`, `docs/cryptography.md`, and ADR records synchronized with implementation.
- Signature identity model moved to hybrid policy (`signer_display` + authoritative `signer_key_id`), with compatibility fields retained.

### Fixed
- CLI error output hardened with passphrase redaction in surfaced exception text.
- Verification now enforces key-ID matching between manifest and verifier public key.

---

## [0.1.0] - 2025-10-15 (Planned)
### Added
- MVP CLI: `seal`, `verify`, `inspect`, `keygen`, `config`, `profile`
- PNG/JPEG support: IPTC/XMP writing, SHA-256, signed `manifest.json`
- Basic profiles and output structure
- Optional provenance ZIP bundle
- Docs: overview, quickstart, cli, config, manifest, file-formats, cryptography, roadmap, faq

### Changed
- N/A

### Fixed
- N/A

[Unreleased]: https://github.com/REPLACE_ORG/REPLACE_REPO/compare/v1.0.0...HEAD
[1.0.0]: https://github.com/REPLACE_ORG/REPLACE_REPO/releases/tag/v1.0.0
[0.1.0-rc1]: https://github.com/REPLACE_ORG/REPLACE_REPO/releases/tag/v0.1.0-rc1
[0.1.0]: https://github.com/REPLACE_ORG/REPLACE_REPO/releases/tag/v0.1.0
