# 0001 - Adopt Python for CLI/Core Implementation

- Status: Accepted
- Date: 2026-03-06

## Context
Sealimg needs a local-first CLI and core library that can iterate quickly while integrating image processing, metadata handling, cryptography, and packaging workflows.

## Decision
Use Python as the primary implementation language for v0.1 (CLI and core library).

## Consequences
- Faster iteration and easier dependency integration for early milestones.
- Packaging/distribution and dependency pinning must be handled carefully for Windows/Linux.
- Performance-sensitive paths may need optimization later, but are acceptable for v0.1 scope.

## Alternatives Considered
- Rust: stronger binary distribution and performance, but slower initial velocity.
- Go: good binaries and concurrency, but less mature ecosystem depth for some metadata/C2PA workflows.
