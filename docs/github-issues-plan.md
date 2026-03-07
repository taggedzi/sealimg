# GitHub Issues Plan

This file converts [TODO.md](/mnt/e/Home/Documents/Programming/sealimg/TODO.md) into GitHub issue candidates for implementation.

## Suggested Labels
- `epic`
- `backend`
- `cli`
- `crypto`
- `metadata`
- `c2pa`
- `testing`
- `docs`
- `security`
- `platform`
- `v0.1`
- `v0.3`
- `v0.5`
- `v0.7`
- `v1.0`

## Suggested Milestones
- `v0.1 MVP`
- `v0.3 Embedding + Batch`
- `v0.5 Watermark + Timestamp`
- `v0.7 Expanded Formats`
- `v1.0 GUI`

## Epic 1: Python Project Foundation (`v0.1 MVP`)
**Title:** `epic: bootstrap python project and delivery pipeline`
**Labels:** `epic`, `backend`, `platform`, `v0.1`
**Body:**
- Stand up Python project layout for library + CLI.
- Add lint/format/test tooling and CI baseline.
- Add fixtures directories and golden artifact structure.
- Target Windows and Linux support.

**Acceptance Criteria**
- Project builds and test runner executes on Windows/Linux in CI.
- Basic package entrypoint for `sealimg` CLI exists.
- Tooling and contribution docs reference actual commands.

### Child issues
1. `build: initialize python package layout for core + cli`
2. `ci: add lint/format/test workflows for windows and linux`
3. `test: add fixture directories and golden artifact conventions`

## Epic 2: Core Models and Config (`v0.1 MVP`)
**Title:** `epic: implement config and manifest domain models`
**Labels:** `epic`, `backend`, `v0.1`
**Body:**
- Implement config model from `docs/config.md`.
- Implement manifest v1 model from `docs/manifest.md`.
- Add schema validation and compatibility/version handling.
- Implement deterministic image ID generation and profile override precedence.

**Acceptance Criteria**
- Config loads/saves with documented keys.
- Manifest JSON validates against internal schema checks.
- Profile merge order is deterministic and tested.

### Child issues
1. `feat: add config parser and writer for ~/.sealimg/config.yml`
2. `feat: add manifest v1 model with strict validation`
3. `feat: implement image id generator and profile merge precedence`

## Epic 3: Key Management and Signatures (`v0.1 MVP`)
**Title:** `epic: key management and signing verification`
**Labels:** `epic`, `crypto`, `security`, `v0.1`
**Body:**
- Implement native crypto-backed keygen/sign/verify.
- Support optional GPG key import/use when provided by user.
- Keep private keys encrypted at rest and prompt for passphrase on signing.
- Add revocation list warning behavior.

**Acceptance Criteria**
- `keygen` supports Ed25519 default and RSA optional.
- `manifest.json` detached signatures verify correctly.
- Tampered manifest fails verification.
- GPG path works when provided keys are valid.

### Child issues
1. `feat: implement keygen (ed25519 default, rsa optional)`
2. `feat: implement key show with public key + fingerprint output`
3. `feat: implement detached signing and verification for manifest.json`
4. `feat: add optional gpg key import/use path`
5. `feat: add key revocation list checks and verify warnings`

## Epic 4: PNG/JPEG Processing and Metadata (`v0.1 MVP`)
**Title:** `epic: implement png/jpeg pipeline and metadata writing`
**Labels:** `epic`, `metadata`, `backend`, `v0.1`
**Body:**
- Support PNG/JPEG ingestion.
- Write IPTC/XMP fields based on `specs/iptc-xmp-mapping.md`.
- Implement pixel-preserving master behavior (metadata/provenance changes allowed).
- Implement web export resize/compression and visible watermark option.

**Acceptance Criteria**
- PNG/JPEG inputs seal successfully.
- Required metadata fields are written and inspectable.
- Master output preserves pixels while allowing metadata updates.
- Web output respects profile dimensions and quality settings.

### Child issues
1. `feat: add png/jpeg readers and normalizers`
2. `feat: write iptc/xmp mappings for author website license and rights`
3. `feat: implement master output with pixel-preserving policy`
4. `feat: implement web export resize quality and visible watermark`
5. `feat: add invisible watermark plugin interface stub (off by default)`

## Epic 5: Manifest Outputs and Packaging (`v0.1 MVP`)
**Title:** `epic: generate manifest hashes and provenance package outputs`
**Labels:** `epic`, `backend`, `cli`, `v0.1`
**Body:**
- Generate SHA-256 hashes for master/web/manifest.
- Write stable `manifest.json` + detached signature.
- Emit `sha256.txt` and `README.txt`.
- Add optional provenance ZIP output.

**Acceptance Criteria**
- Output directory contains expected artifacts per sealed image.
- Hashes verify against manifest.
- Optional ZIP includes all required files.

### Child issues
1. `feat: generate sha256 for artifacts and write sha256.txt`
2. `feat: write package readme from template`
3. `feat: add provenance zip bundling option`

## Epic 6: C2PA Sidecar-First Embedding (`v0.3 Embedding + Batch`)
**Title:** `epic: implement sidecar-first c2pa embedding strategy`
**Labels:** `epic`, `c2pa`, `metadata`, `v0.3`
**Body:**
- Always emit sidecar manifest/signature.
- Attempt best-effort embedding for JPEG and PNG.
- Do not fail sealing when embed is unsupported/fails (unless future strict mode is added).

**Acceptance Criteria**
- Embed attempt status is reported in command output.
- Sidecar verification remains valid when embedding fails.
- Inspect command can report embedded/sidecar provenance state.

### Child issues
1. `research: select python-compatible metadata and c2pa libraries for png/jpeg`
2. `feat: add jpeg jumbf/app11 embedding adapter`
3. `feat: add png ancillary chunk embedding adapter`
4. `feat: add embed status reporting in seal and inspect`

## Epic 7: CLI Command Surface (`v0.1 MVP`)
**Title:** `epic: implement cli commands and exit code contract`
**Labels:** `epic`, `cli`, `v0.1`
**Body:**
- Implement documented commands:
  - `seal`
  - `verify`
  - `inspect`
  - `keygen`, `key show`
  - `config set/get`
  - `profile list/show/add`
- Enforce exit codes 0/1/2/3.

**Acceptance Criteria**
- CLI help and behavior match `docs/cli.md`.
- Exit codes are deterministic and tested.
- Batch folder sealing works with `--recursive`.

### Child issues
1. `feat: implement seal command and output directory contract`
2. `feat: implement verify command with signature hash and embed checks`
3. `feat: implement inspect command with plain-english output`
4. `feat: implement config and profile command groups`
5. `test: add cli exit code tests for success failure verify-fail and unsupported`

## Epic 8: Test Suite and Cross-Platform Quality (`v0.1 MVP`)
**Title:** `epic: implement test plan and quality gates`
**Labels:** `epic`, `testing`, `security`, `platform`, `v0.1`
**Body:**
- Implement tests from `design/test-plan.md`.
- Cover functional, mutation, crypto, metadata, regression, and platform cases.
- Ensure sensitive data is never logged.

**Acceptance Criteria**
- All required test categories have coverage and fixtures.
- Windows/Linux CI includes cross-platform path cases.
- Security checks confirm no passphrase/key leakage in logs.

### Child issues
1. `test: functional sealing and verification for png and jpeg`
2. `test: mutation tests for tampering metadata stripping and hash mismatch`
3. `test: cross-platform filename and path edge cases`
4. `test: golden snapshot tests for manifest stability`
5. `security: verify passphrases and private key material are never logged`

## Epic 9: Documentation and Release Readiness (`v0.1 MVP`)
**Title:** `epic: finalize documentation for first release`
**Labels:** `epic`, `docs`, `v0.1`
**Body:**
- Replace quickstart install placeholder with real instructions.
- Keep CLI docs synchronized with implemented flags/behavior.
- Add embed compatibility matrix and trust/key-sharing guidance.
- Update changelog for first implemented release.

**Acceptance Criteria**
- Quickstart is executable as written.
- CLI/reference docs match actual command behavior.
- Changelog reflects shipped functionality only.

### Child issues
1. `docs: publish install and setup instructions for windows and linux`
2. `docs: sync cli and config references to implementation`
3. `docs: add c2pa/embed compatibility matrix by format and platform`
4. `docs: add public key sharing trust and revocation guidance`
5. `docs: prepare changelog entries for v0.1 implementation`

## Post-v0.1 Backlog Epics

### Epic 10 (`v0.3 Embedding + Batch`)
**Title:** `epic: add watch mode and high-throughput batch workflows`
**Labels:** `epic`, `cli`, `v0.3`

### Epic 11 (`v0.5 Watermark + Timestamp`)
**Title:** `epic: implement invisible watermark and timestamp helper`
**Labels:** `epic`, `metadata`, `crypto`, `v0.5`

### Epic 12 (`v0.7 Expanded Formats`)
**Title:** `epic: add avif heic jpeg-xl and recipient fingerprinting`
**Labels:** `epic`, `c2pa`, `v0.7`

### Epic 13 (`v1.0 GUI`)
**Title:** `epic: deliver local gui and integration guides`
**Labels:** `epic`, `docs`, `v1.0`

## Execution Order
1. Epic 1: Foundation
2. Epic 2: Models/Config
3. Epic 3: Crypto/Keys
4. Epic 4: PNG/JPEG + Metadata
5. Epic 5: Manifest/Packaging
6. Epic 7: CLI Command Surface
7. Epic 8: Test Suite
8. Epic 9: Docs/Release
9. Epic 6: C2PA Embedding (can run partly in parallel once output pipeline exists)
10. Post-v0.1 backlog epics (10-13)

## Bootstrap Automation
- Use `scripts/bootstrap_github_project.sh` to create labels, milestones, and epics via GitHub CLI.
- Run from repo root after `gh auth login`.
