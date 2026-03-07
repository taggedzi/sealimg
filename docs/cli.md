# CLI Reference (Draft)

> Flags and output may evolve during v0.x releases.

## Commands

### `sealimg keygen`
Create a signing keypair.
```
sealimg keygen [--ed25519|--rsa] [--name "Display Name"] \
  [--key-name NAME] [--output-dir PATH] \
  [--passphrase "..."] [--write-config] [--config-path PATH] [--verbose]
```

### `sealimg key show`
Show public key / fingerprint.
```
sealimg key show <public_key.pem> [--fingerprint | --pubkey]
```

### `sealimg config`
Set or view defaults.
```
sealimg config set --author "Name" --site "https://..." --license "CC BY-NC 4.0" \
  --output-root "./sealed" --default-profile "web" \
  --signing-key "~/.sealimg/keys/you_ed25519.key"
sealimg config get [--config-path PATH]
```

### `sealimg profile`
List/manage export presets.
```
sealimg profile list [--config-path PATH]
sealimg profile show web [--config-path PATH]
sealimg profile add web --long-edge 2560 --quality 82 \
  --wm-visible on --wm-invisible off --wm-style diag-low --wm-text "© You • site"
```

### `sealimg seal`
Seal images or folders.
```
sealimg seal <paths...> [--recursive] [--profile NAME]
[--wm-visible on|off] [--wm-invisible on|off]
[--bundle on|off] [--no-embed] [--id-prefix "IMG-"]
[--author "..."] [--site "..."] [--license "..."]
[--output-root PATH] [--signing-key PATH]
[--passphrase "..."] [--config-path PATH] [--json]
[--timestamp-log PATH] [--timestamp-post-url URL]
```

### `sealimg watch`
Watch a directory and seal newly discovered images.
```
sealimg watch <directory> [--recursive] [--profile NAME]
[--wm-visible on|off] [--wm-invisible on|off]
[--bundle on|off] [--no-embed] [--id-prefix "IMG-"]
[--author "..."] [--site "..."] [--license "..."]
[--output-root PATH] [--signing-key PATH] [--passphrase "..."]
[--interval 2.0] [--once] [--json]
[--timestamp-log PATH] [--timestamp-post-url URL]
```

### `sealimg verify`
Verify a sealed image or manifest.
```
sealimg verify <image-or-manifest> [--pubkey PATH] [--config-path PATH] [--json]
```

Verification checks:
- Signature validity
- Signer key ID match (public key fingerprint against manifest key ID)
- File hash consistency (`master`, `web`)
- Embedded marker detection status

### `sealimg inspect`
Prints metadata and embedded structures in plain English.
```
sealimg inspect <image> [--json]
```

## Exit Codes
- `0` success
- `1` generic error
- `2` verification failed (invalid signature or mismatched hash)
- `3` unsupported format

## Machine-Readable Output
- `seal --json`: emits summary JSON with outputs per input.
- `verify --json`: emits signature/hash/embed status JSON and exit code compatibility.
- `inspect --json`: emits image format/size/metadata/embed status JSON.
