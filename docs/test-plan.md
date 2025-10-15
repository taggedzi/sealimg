# Test Plan

## Functional
- Seal single PNG/JPEG; verify outputs exist.
- Verify manifest signature with independent tool.
- Inspect IPTC/XMP fields present and correct.
- Attempt C2PA embed; confirm discoverable (where supported).

## Mutation
- Recompress/crop web copy; confirm manifest still verifies (for the original files) and that C2PA presence is reported accurately.
- Strip metadata; confirm sidecar verification still passes.

## Cross-Platform
- Windows/macOS/Linux basic flows.
- Long paths, non-ASCII filenames.

## Security
- Key generation entropy check.
- Encrypted private key storage.
- Passphrase never logged.

## Regression
- Golden fixtures (known hashes/signatures).
- Snapshot tests for manifest schema stability.
