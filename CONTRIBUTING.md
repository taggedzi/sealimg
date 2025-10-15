# Contributing to Sealimg

First off, thanks for taking the time to contribute.
This document explains how to propose changes, report issues, and submit PRs.

## Table of Contents
- [Code of Conduct](#code-of-conduct)
- [How Can I Help?](#how-can-i-help)
- [Reporting Bugs](#reporting-bugs)
- [Proposing Enhancements](#proposing-enhancements)
- [Pull Requests](#pull-requests)
- [Design & Docs](#design--docs)
- [Style & Commit Messages](#style--commit-messages)
- [Versioning](#versioning)
- [Release Process](#release-process)

## Code of Conduct
By participating, you agree to abide by our [Code of Conduct](CODE_OF_CONDUCT.md).

## How Can I Help?
- File issues for bugs and feature requests.
- Improve documentation (README, /docs, /design, /specs).
- Create minimal test images/fixtures for verification.
- Add platform support (Windows/macOS/Linux) or new formats (AVIF/HEIC/JPEG XL).
- Improve CLI UX and error messages.

## Reporting Bugs
- Search existing issues to avoid duplicates.
- Include:
  - OS and version
  - Sealimg version (or commit SHA)
  - Exact command(s) run
  - Expected vs actual behavior
  - Minimal repro steps and sample files (if possible)

## Proposing Enhancements
- Open an issue titled `RFC: <feature-name>`.
- Describe the problem first, then the proposed solution.
- Call out trade-offs, alternatives, and any breaking changes.

## Pull Requests
1. Fork the repo and create a feature branch:  
   `git checkout -b feat/short-description`
2. Keep PRs focused and small; open draft PRs early if helpful.
3. Add/update docs for user-facing changes.
4. Add tests or sample fixtures where sensible.
5. Ensure `README` or `docs/` reflect new flags/behavior.
6. Link the issue being fixed: `Fixes #123`.

### PR Checklist
- [ ] Tests / fixtures added or updated (if applicable)
- [ ] Docs updated (README or /docs)
- [ ] Conventional commit message (see below)
- [ ] CI passes locally (if applicable)

## Design & Docs
- Major changes should include a short design note under `/design` or `/specs`.
- Keep manifests and formats human-readable; prefer additive changes.

## Style & Commit Messages
- Prefer **Conventional Commits**:
  - `feat: add AVIF embedding`
  - `fix: handle EXIF-less PNG gracefully`
  - `docs: clarify key backup`
  - `refactor: split verify into subcommands`
  - `test: add golden fixtures for jpeg-jumbf`
- Keep commit messages imperative and concise.
- For code style (once code exists), follow language-idiomatic linters/formatters.

## Versioning
- Use **Semantic Versioning** (SemVer): `MAJOR.MINOR.PATCH`.
- Breaking changes bump MAJOR and must be called out in `CHANGELOG.md`.

## Release Process
1. Update `CHANGELOG.md`.
2. Tag the release: `vX.Y.Z`.
3. Build and attach artifacts (if any).
4. Publish release notes.
