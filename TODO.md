# Sealimg Implementation TODO

This TODO is derived from `README.md`, `docs/`, `design/`, and `specs/` and is intended to be sufficient to build the application described in this repository.

## 0) Project Setup
- [ ] Choose primary implementation language/runtime for CLI core.
- [ ] Initialize project structure for:
  - [ ] Core sealing library
  - [ ] CLI interface
  - [ ] Format adapters (PNG/JPEG first)
  - [ ] Crypto/key management
  - [ ] Verification/inspection
- [ ] Add linting, formatting, test runner, and CI baseline.
- [ ] Add fixture directories for sample images and golden manifests/signatures.

## 1) Core Domain Models
- [x] Implement `config.yml` model from `docs/config.md`.
- [x] Implement manifest v1 model from `docs/manifest.md`.
- [x] Add strict manifest schema validation and version field handling.
- [x] Implement deterministic image ID generator (`YYYYMMDD-####` or configured prefix).
- [x] Implement profile resolution (config defaults < profile < CLI overrides).

## 2) Key Management & Signing
- [ ] Implement `sealimg keygen`:
  - [ ] Ed25519 default
  - [ ] RSA-2048+ optional
  - [ ] Import existing key path support
- [ ] Encrypt private keys at rest and enforce passphrase prompt on signing.
- [ ] Implement `sealimg key show` (public key and fingerprint output).
- [ ] Implement detached signature generation for `manifest.json` -> `manifest.sig`.
- [ ] Implement signature verification independent of embed status.
- [ ] Add revocation list support (local text file + verify warning state).

## 3) Metadata & File Processing
- [ ] Add PNG/JPEG input loading and normalization.
- [ ] Implement IPTC/XMP writing for:
  - [ ] Author
  - [ ] Website
  - [ ] License
  - [ ] Copyright/title/description where provided
- [ ] Implement master output generation (no visual pixel edits intended).
- [ ] Implement web output generation:
  - [ ] Resize by profile long edge
  - [ ] JPEG quality/profile controls
  - [ ] Optional visible watermark text/style
- [ ] Implement optional invisible watermark plugin interface (stub for v0.1, implementation by v0.5).

## 4) Manifest, Hashes, and Packaging
- [ ] Generate SHA-256 for `master`, `web`, and `manifest.json`.
- [ ] Build manifest with required/optional fields in stable ordering.
- [ ] Write `sha256.txt` output for human/tool verification.
- [ ] Emit package README (`README.txt`) based on `examples/sample-readme.txt`.
- [ ] Implement optional provenance ZIP bundle with:
  - [ ] master
  - [ ] web
  - [ ] manifest.json
  - [ ] manifest.sig
  - [ ] sha256.txt
  - [ ] README.txt

## 5) C2PA / Embedding Strategy
- [ ] Implement sidecar-first contract: always produce `manifest.json` + `manifest.sig`.
- [ ] Implement best-effort embed attempt:
  - [ ] JPEG JUMBF/APP11 path
  - [ ] PNG ancillary chunk path
- [ ] Record embed success/failure in CLI output and inspect results.
- [ ] Ensure sealing continues when embed fails (no hard failure unless explicitly requested).
- [ ] Define adapter boundary for future AVIF/HEIC/JPEG XL.

## 6) CLI Commands (MVP)
- [ ] Implement `sealimg seal <paths...>`:
  - [ ] files + directories + `--recursive`
  - [ ] profile selection and overrides
  - [ ] `--wm-visible`, `--wm-invisible`, `--bundle`, `--no-embed`, `--id-prefix`
  - [ ] output under `/sealed/<image_id>/`
- [ ] Implement `sealimg verify <image-or-manifest>`:
  - [ ] signature validation
  - [ ] hash matching
  - [ ] embed presence/status
  - [ ] clear pass/fail summary
- [ ] Implement `sealimg inspect <image>` for plain-English metadata/provenance output.
- [ ] Implement `sealimg config set/get`.
- [ ] Implement `sealimg profile list/show/add`.
- [ ] Implement documented exit codes: `0`, `1`, `2`, `3`.

## 7) Reliability, Safety, and UX
- [ ] Ensure private key/passphrase never printed or logged.
- [ ] Add friendly, actionable errors for unsupported formats and missing keys.
- [ ] Add deterministic output for CI use (machine-readable mode).
- [ ] Add watch/batch behavior backlog item for v0.3.
- [ ] Add timestamp helper backlog item for v0.5 (`hashes.txt` + optional POST hook).

## 8) Test Plan Implementation
- [ ] Functional tests:
  - [ ] seal PNG
  - [ ] seal JPEG
  - [ ] verify outputs exist and parse
- [ ] Crypto tests:
  - [ ] signature validates with independent verifier
  - [ ] tampered manifest fails verification
- [ ] Metadata tests:
  - [ ] IPTC/XMP mappings match `specs/iptc-xmp-mapping.md`
- [ ] Embed tests:
  - [ ] embed success path (where library support exists)
  - [ ] sidecar fallback path
- [ ] Mutation tests:
  - [ ] metadata stripped case still verifies via sidecar
  - [ ] modified file causes hash mismatch
- [ ] Cross-platform tests:
  - [ ] Windows/macOS/Linux paths
  - [ ] non-ASCII filenames
- [ ] Regression fixtures:
  - [ ] golden manifest snapshots
  - [ ] golden hashes/signatures

## 9) Documentation Completion Gates
- [ ] Replace install placeholder in `docs/quickstart.md` with real instructions.
- [ ] Keep `docs/cli.md` synchronized with implemented flags and examples.
- [ ] Add compatibility matrix for embed support by format/OS/library.
- [ ] Publish public key sharing and trust guidance in docs.
- [ ] Update `CHANGELOG.md` for first real release.

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
