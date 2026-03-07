# AGENTS.md

This file is the operational handoff for future contributors and coding agents working in this repository.

## Project State
- Repository now includes a working Python implementation and test suite.
- Current release state: `v0.1.0-rc1` is prepared in `CHANGELOG.md` and smoke-tested manually.
- Primary implementation plan remains tracked in `TODO.md`.
- GitHub issue decomposition remains tracked in `docs/github-issues-plan.md`.

## Local Environment Notes
- Primary (Windows/PowerShell) virtual environment is `./.venv`.
- WSL/Ubuntu virtual environment is `./.ubuntu-venv`.
- Preferred activation from repo root:
  - Windows/PowerShell: `.\.venv\Scripts\Activate.ps1`
  - Linux/WSL: `source .ubuntu-venv/bin/activate`
- Use the active platform venv for dependency install, linting, and test execution.
- Tool readiness confirmed:
  - `git` installed
  - `gh` installed and authenticated
  - `pwsh` installed (`7.5.4`)

## Confirmed Decisions (Authoritative)
1. Implementation stack: Python.
2. Crypto strategy: native crypto libraries for core features, with optional GPG key import/use when users provide keys.
3. Master file policy: pixel-preserving master; metadata/provenance updates are allowed; byte-identical output is not required.
4. v0.1 target platforms: Windows and Linux.
5. Project execution management: GitHub Issues should be used to track work.
6. Signature identity policy: hybrid (`signer_display` for UX + authoritative `signer_key_id` for verification).
7. Metadata/C2PA strategy: staged hybrid (v0.1 best-effort local embedding + sidecar-first, strict backend path later).

See `docs/adr/` for full decision records.

## Source of Truth Priority
When documentation conflicts, use this order:
1. `docs/adr/*.md` (accepted decisions)
2. `TODO.md` (implementation checklist)
3. `docs/github-issues-plan.md` (work breakdown)
4. `README.md` + `docs/*` + `design/*` + `specs/*`

## Implementation Start Order
1. Foundation and tooling (`v0.1`): package layout, lint/format/test, CI.
2. Domain models: config + manifest + profile resolution + image ID generation.
3. Crypto/key flows: keygen/show/sign/verify + optional GPG path.
4. PNG/JPEG pipeline: metadata writing, master/web outputs.
5. Manifest packaging: hashes, signature, README, optional ZIP.
6. CLI commands and exit code contract.
7. Full test plan implementation and docs sync.

## Guardrails
- Keep sidecar-first provenance contract: always emit `manifest.json` + `manifest.sig`.
- Treat C2PA embedding as best-effort (non-blocking unless strict mode is intentionally added later).
- Do not claim byte-identical master outputs.
- Keep passphrases/private keys out of logs and command output.
- Preserve cross-platform behavior for Windows and Linux.

## Working Conventions
- Use one issue per concrete task and reference its parent epic.
- For major architecture changes, add/update ADRs before implementation.
- Keep docs updated in the same PR for user-visible behavior changes.
- Maintain test fixtures and golden artifacts as behavior evolves.

## Next Actions (if resuming work)
1. Keep PR-only branch workflow active:
   - all changes on feature branches
   - signed commits required
   - merge via PR after required checks pass
2. Complete follow-up issue #14:
   - clarify per-artifact embed-status messaging for `master` and `web`
   - keep JSON output stable for `seal`, `verify`, and `inspect`
   - add mixed-result tests and docs examples
3. Begin next roadmap milestone:
   - v0.5 invisible watermark implementation
   - v0.5 public timestamp helper improvements

## Session Handoff (2026-03-07)
- Stop point: manual release smoke sequence completed successfully in WSL (`.ubuntu-venv`).
- Smoke sequence results:
  - `seal` (single): pass
  - `seal` (batch): pass
  - `watch --once`: pass
  - `verify --json`: pass (`hash_valid=true`, `signature_valid=true`, `key_id_match=true`)
  - `inspect --json`: pass
- Notes:
  - Key path mismatch was resolved by setting `--signing-key .smoke/keys/sealimg_ed25519.key`.
  - `main` has been pushed to `origin/main`.
  - User temporarily removed required-commit-signing branch rule; intention is to restore strong signing/protection policy later for evidentiary integrity.
