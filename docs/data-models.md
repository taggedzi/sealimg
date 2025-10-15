# Data Models (Draft)

## Config
- author, website, license, default_profile, output_root, signing_key
- profiles: named maps of export settings

## Manifest (v1)
- `schema`, `image_id`, `author`, `website`, `license`
- `files.master`/`files.web`: `path`, `sha256`
- `timestamps`: `local_created`, `sealed_utc`, optional `public_proof`
- `watermarks`: `visible`, `invisible`
- `source`: `ai_assisted`, `ai_base`, `edited_by_human`, `tools[]`
- `signature`: `algo`, `signer`, `pubkey_fingerprint`, `signature_file`
- `notes`, `links[]`
