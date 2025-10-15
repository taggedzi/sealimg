# CLI Reference (Draft)

> Flags and output may evolve during v0.x releases.

## Commands

### `sealimg keygen`
Create or import a signing key.
```

sealimg keygen [--ed25519|--rsa] [--name "Display Name"] [--import <path>]

```

### `sealimg key show`
Show public key / fingerprint.
```

sealimg key show [--fingerprint | --pubkey]

```

### `sealimg config`
Set or view defaults.
```

sealimg config set --author "Name" --site "https://..." --license "CC BY-NC 4.0" 
--output-root "./sealed" --default-profile "web" --signing-key "~/.sealimg/keys/you.key"
sealimg config get

```

### `sealimg profile`
List/manage export presets.
```

sealimg profile list
sealimg profile show web
sealimg profile add web --long-edge 2560 --quality 82 --wm-visible on

```

### `sealimg seal`
Seal images or folders.
```

sealimg seal <paths...> [--recursive] [--profile NAME]
[--wm-visible on|off] [--wm-invisible on|off]
[--bundle on|off] [--no-embed] [--id-prefix "IMG-"]

```

### `sealimg verify`
Verify a sealed image or manifest.
```

sealimg verify <image-or-manifest>

```

### `sealimg inspect`
Prints metadata and embedded structures in plain English.
```

sealimg inspect <image>

```

## Exit Codes
- `0` success
- `1` generic error
- `2` verification failed (invalid signature or mismatched hash)
- `3` unsupported format
