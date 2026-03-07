# AGENT.md

This file is the operational handoff for future contributors and coding agents working in this repository.

## Project State
- This repository is currently documentation-first (no implementation code yet).
- Primary implementation plan is tracked in `TODO.md`.
- GitHub issue decomposition is tracked in `docs/github-issues-plan.md`.

## Confirmed Decisions (Authoritative)
1. Implementation stack: Python.
2. Crypto strategy: native crypto libraries for core features, with optional GPG key import/use when users provide keys.
3. Master file policy: pixel-preserving master; metadata/provenance updates are allowed; byte-identical output is not required.
4. v0.1 target platforms: Windows and Linux.
5. Project execution management: GitHub Issues should be used to track work.

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
1. Create repository labels and milestones listed in `docs/github-issues-plan.md`.
2. Create Epics 1-9 from the plan.
3. Start implementation with Epic 1 child issues.
