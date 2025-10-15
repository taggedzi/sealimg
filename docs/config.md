# Configuration & Profiles

## Config File
Default: `~/.sealimg/config.yml`

### Keys
- `author`: default author string.
- `website`: your homepage or portfolio URL.
- `license`: default license string (e.g., "CC BY-NC 4.0").
- `default_profile`: profile name for `sealimg seal`.
- `output_root`: where sealed folders are written.
- `signing_key`: path to encrypted private key.

### Example
```yaml
author: "Matthew Craig"
website: "https://taggedz.me"
license: "CC BY-NC 4.0"
default_profile: "web"
output_root: "./sealed"
signing_key: "~/.sealimg/keys/matthew_ed25519.key"
profiles:
  web:
    long_edge: 2560
    jpeg_quality: 82
    wm_visible:
      enabled: true
      text: "© Matthew Craig • taggedz.me"
      style: "diag-low"
    wm_invisible:
      enabled: false
  print:
    long_edge: 6000
    jpeg_quality: 95
    wm_visible:
      enabled: false
    wm_invisible:
      enabled: true
````

## Profiles

Profiles define export behavior per use-case (web, print, portfolio). CLI flags override profile values.
