# Sealimg Implementation TODO

This TODO is derived from `README.md`, `docs/`, `design/`, and `specs/` and is intended to be sufficient to build the application described in this repository.

## 0) Project Setup
- [x] Choose primary implementation language/runtime for CLI core.
- [x] Initialize project structure for:
  - [x] Core sealing library
  - [x] CLI interface
  - [x] Format adapters (PNG/JPEG first)
  - [x] Crypto/key management
  - [x] Verification/inspection
- [x] Add linting, formatting, test runner, and CI baseline.
- [x] Add fixture directories for sample images and golden manifests/signatures.

## 1) Core Domain Models
- [x] Implement `config.yml` model from `docs/config.md`.
- [x] Implement manifest v1 model from `docs/manifest.md`.
- [x] Add strict manifest schema validation and version field handling.
- [x] Implement deterministic image ID generator (`YYYYMMDD-####` or configured prefix).
- [x] Implement profile resolution (config defaults < profile < CLI overrides).

## 2) Key Management & Signing
- [x] Implement `sealimg keygen`:
  - [x] Ed25519 default
  - [x] RSA-2048+ optional
  - [x] Import existing key path support
- [x] Encrypt private keys at rest and enforce passphrase prompt on signing.
- [x] Implement `sealimg key show` (public key and fingerprint output).
- [x] Implement detached signature generation for `manifest.json` -> `manifest.sig`.
- [x] Implement signature verification independent of embed status.
- [x] Add revocation list support (local text file + verify warning state).

## 3) Metadata & File Processing
- [x] Add PNG/JPEG input loading and normalization.
- [x] Implement IPTC/XMP writing for:
  - [x] Author
  - [x] Website
  - [x] License
  - [x] Copyright/title/description where provided
- [x] Implement master output generation (no visual pixel edits intended).
- [x] Implement web output generation:
  - [x] Resize by profile long edge
  - [x] JPEG quality/profile controls
  - [x] Optional visible watermark text/style
- [x] Implement optional invisible watermark plugin interface (stub for v0.1, implementation by v0.5).

## 4) Manifest, Hashes, and Packaging
- [x] Generate SHA-256 for `master`, `web`, and `manifest.json`.
- [x] Build manifest with required/optional fields in stable ordering.
- [x] Write `sha256.txt` output for human/tool verification.
- [x] Emit package README (`README.txt`) based on `examples/sample-readme.txt`.
- [x] Implement optional provenance ZIP bundle with:
  - [x] master
  - [x] web
  - [x] manifest.json
  - [x] manifest.sig
  - [x] sha256.txt
  - [x] README.txt

## 5) C2PA / Embedding Strategy
- [x] Implement sidecar-first contract: always produce `manifest.json` + `manifest.sig`.
- [x] Implement best-effort embed attempt:
  - [x] JPEG JUMBF/APP11 path
  - [x] PNG ancillary chunk path
- [x] Record embed success/failure in CLI output and inspect results.
- [x] Ensure sealing continues when embed fails (no hard failure unless explicitly requested).
- [x] Define adapter boundary for future AVIF/HEIC/JPEG XL.

## 6) CLI Commands (MVP)
- [x] Implement `sealimg seal <paths...>`:
  - [x] files + directories + `--recursive`
  - [x] profile selection and overrides
  - [x] `--wm-visible`, `--wm-invisible`, `--bundle`, `--no-embed`, `--id-prefix`
  - [x] output under `/sealed/<image_id>/`
- [x] Implement `sealimg verify <image-or-manifest>`:
  - [x] signature validation
  - [x] hash matching
  - [x] embed presence/status
  - [x] clear pass/fail summary
- [x] Implement `sealimg inspect <image>` for plain-English metadata/provenance output.
- [x] Implement `sealimg config set/get`.
- [x] Implement `sealimg profile list/show/add`.
- [x] Implement documented exit codes: `0`, `1`, `2`, `3`.

## 7) Reliability, Safety, and UX
- [x] Ensure private key/passphrase never printed or logged.
- [x] Add friendly, actionable errors for unsupported formats and missing keys.
- [x] Add deterministic output for CI use (machine-readable mode).
- [ ] Add watch/batch behavior backlog item for v0.3.
- [ ] Add timestamp helper backlog item for v0.5 (`hashes.txt` + optional POST hook).

## 8) Test Plan Implementation
- [x] Functional tests:
  - [x] seal PNG
  - [x] seal JPEG
  - [x] verify outputs exist and parse
- [ ] Crypto tests:
  - [x] signature validates with independent verifier
  - [x] tampered manifest fails verification
- [ ] Metadata tests:
  - [ ] IPTC/XMP mappings match `specs/iptc-xmp-mapping.md`
- [ ] Embed tests:
  - [x] embed success path (where library support exists)
  - [x] sidecar fallback path
- [ ] Mutation tests:
  - [ ] metadata stripped case still verifies via sidecar
  - [x] modified file causes hash mismatch
- [ ] Cross-platform tests:
  - [ ] Windows/macOS/Linux paths
  - [ ] non-ASCII filenames
- [ ] Regression fixtures:
  - [x] golden manifest snapshots
  - [x] golden hashes/signatures

## 9) Documentation Completion Gates
- [x] Replace install placeholder in `docs/quickstart.md` with real instructions.
- [x] Keep `docs/cli.md` synchronized with implemented flags and examples.
- [x] Add compatibility matrix for embed support by format/OS/library.
- [x] Publish public key sharing and trust guidance in docs.
- [x] Update `CHANGELOG.md` for first real release.

## 10) Milestone Mapping
- [ ] v0.1: CLI + PNG/JPEG + metadata + signed manifest + verify + config/profiles.
- [ ] v0.3: C2PA best-effort embed + provenance ZIP + watch/batch.
- [ ] v0.5: invisible watermark + public timestamp helper.
- [ ] v0.7: AVIF/HEIC/JPEG XL + recipient fingerprinting + pHash.
- [ ] v1.0: GUI + integration guides.

## Decisions Needed Before Implementation Starts
- [x] Select implementation stack (language/runtime and packaging target): Python.
- [x] Select crypto backend/library strategy: native crypto libraries for core features, with optional GPG key import/use when users provide keys.
- [ ] Select metadata/C2PA libraries for PNG/JPEG embedding.
- [x] Define `master` policy: pixel-preserving master where metadata/provenance changes are allowed; not guaranteed byte-identical to original file.
- [ ] Decide signing identity format (free text name vs key-bound UID policy).
- [x] Decide minimum supported OS versions for v0.1: Windows and Linux.
- [x] Issue tracking approach: use GitHub Issues to map TODO execution if repository issue tracking is available.
