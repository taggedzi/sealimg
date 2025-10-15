# Project: **Sealimg** (working name)

*A tiny, local, open-source tool that “seals” images with provenance so artists can share freely and sleep at night.*

## 1) Vision & Non-Goals

**Vision:** One-button “Save & Sign” for images: add clear authorship + usage info, embed a signed provenance manifest (C2PA-compatible), write human-readable metadata, (optionally) add an invisible watermark, and export a ready-to-publish web copy—without cloud accounts or subscriptions.

**Non-Goals (v1):**

* Not a DAM or CMS.
* Not a legal service.
* No cloud back-end; all local/offline.
* No proprietary vendor lock-ins.

---

## 2) Personas & Use Cases

* **Solo artist**: Drag a folder of images → get sealed masters + web copies.
* **Photographer/Designer**: Batch-seal exports on delivery.
* **Developer/Publisher**: CI step that seals assets pre-deployment.
* **User/SmileCMS**: Ingests sealed images; shows “Provenance” badge and link.

---

## 3) MVP Scope (v0.1–v0.3)

**Input:** PNG/JPEG (later: AVIF/HEIC/JPEG XL).
**Core outputs per image:**

* `master` (lossless copy, untouched pixels).
* `web` (resized/compressed, optional visible watermark).
* **Embedded metadata** (IPTC/XMP: author, website, license).
* **Provenance manifest** (JSON, C2PA-compatible minimal claim).
* **Digital signature** over manifest (GPG/Ed25519).
* **SHA-256 hashes** (master + web).
* **README.txt** (human summary, license).
* **Provenance bundle** (optional ZIP: master + manifest + hashes).

**CLI (examples):**

* `sealimg seal input/*.png --author "Matthew Craig" --site "https://taggedz.me" --license "CC BY-NC 4.0" --profile web`
* `sealimg verify image.jpg` (prints manifest + signature status)

**Defaults that “just work”:**

* Image ID auto: `YYYYMMDD-####`.
* Web size long edge 2560px, quality ~82.
* Visible watermark: low-contrast diagonal `© Name • domain`.
* SHA-256 always; MD5 never.
* Store output in `/sealed/<image_id>/…`

---

## 4) Phase 2 (v0.4–v0.6)

* **Invisible watermark** (toggle) storing `image_id + short_signature`.
* **Public timestamp helpers**:

  * Append manifest hash to a local `hashes.txt` and optionally POST to a user-configured endpoint (e.g., your website).
* **Profiles** (`wallpaper`, `portfolio`, `print`) with tunable sizes/watermark styles.
* **Batch & watch mode**: seal new files dropped into a folder.
* **Extractor/Inspector**: show all embedded metadata + provenance in plain English.

---

## 5) Phase 3 (v0.7–1.0)

* **GUI** (local, minimal): drag-drop → sealed bundle.
* **Per-recipient fingerprinting** (license deliveries).
* **pHash output** to support later web monitoring.
* **AVIF/HEIC/JPEG XL** full C2PA/JUMBF embedding.

---

## 6) Architecture Overview

**Local-only pipeline:**

```
[Input image] 
   → Read metadata
   → Assign image_id
   → Write/merge IPTC/XMP (author/site/license)
   → (Optional) embed invisible watermark(payload=image_id)
   → Create master copy (no pixel change, just metadata/c2pa)
   → Generate web copy (resize/compress, visible watermark)
   → Compute SHA-256 (master, web)
   → Build manifest.json (fields below)
   → Sign manifest (GPG/Ed25519)
   → Embed C2PA claim (JUMBF/box inside image where supported)
   → Emit provenance bundle (optional ZIP)
   → Write README.txt
```

**Key design choices:**

* **Manifests are signed JSON files** (human-readable); signatures verify with user’s public key.
* **C2PA embed**: when filetype supports it, embed the manifest digest + claim; otherwise keep the JSON sidecar + ZIP bundle.
* **Separation of concerns**: sealing logic = pure library; CLI/GUI are thin layers.

---

## 7) Data Model (Manifest v1)

`manifest.json` (minimal, friendly, stable):

```json
{
  "schema": "https://sealimg.org/provenance/v1",
  "image_id": "IMG-2025-10-15-0007",
  "title": "Optional",
  "author": "Matthew Craig",
  "website": "https://taggedz.me",
  "license": "CC BY-NC 4.0",
  "source": {
    "ai_assisted": true,
    "ai_base": "Midjourney",
    "edited_by_human": true,
    "tools": ["GIMP", "Krita"]
  },
  "files": {
    "master": {"path": "master.png", "sha256": "<hex>"},
    "web": {"path": "web.jpg", "sha256": "<hex>"}
  },
  "watermarks": {
    "visible": {"applied": true, "style": "diag-low", "text": "© Matthew Craig • taggedz.me"},
    "invisible": {"applied": false, "payload": null}
  },
  "timestamps": {
    "sealed_utc": "2025-10-15T07:12:20Z",
    "local_created": "2025-10-15T03:12:05-04:00",
    "public_proof": "optional: posted hash line or URL"
  },
  "signature": {
    "algo": "ed25519|rsa",
    "signer": "Matthew Craig",
    "pubkey_fingerprint": "<short>",
    "signature_file": "manifest.sig"
  },
  "notes": "Links to DeviantArt page, prior publication dates, DMCA IDs."
}
```

**Why:** human-readable, easy to diff, and simple to verify.

---

## 8) File Format Support Order

1. **PNG/JPEG** (broadest compatibility)
2. **AVIF/HEIC** (ISOBMFF boxes; better JUMBF support)
3. **JPEG XL** (if/when the toolchain is stable on target OSes)

Fallback: if embedding C2PA isn’t supported, keep signed `manifest.json` + `manifest.sig` alongside the image and include both in the provenance ZIP.

---

## 9) Cryptography & Keys

* **Hashes:** SHA-256.
* **Signatures:** Ed25519 (preferred) or RSA-2048+.
* **Key storage:** local keystore directory; private key encrypted with passphrase.
* **Exports:** provide public key file for sharing/verification.
* **Revocation:** simple text file listing revoked keys + dates.

UX goals:

* First run → generates keypair (or import existing GPG key).
* Passphrase prompt only when signing.
* “Print my public key” command.

---

## 10) CLI Spec (no code, just behavior)

* `sealimg seal <path(s)> [--author --site --license --profile --wm-visible --wm-invisible --bundle --no-embed]`
* `sealimg verify <image-or-manifest>` → prints validity (hashes, signature, embed status) and a friendly summary.
* `sealimg inspect <image>` → dumps IPTC/XMP + C2PA blocks + summary.
* `sealimg keygen [--ed25519|--rsa]` → create/import keys.
* `sealimg config` → set defaults (author, site, license, output dirs).
* `sealimg profile list/add/show` → define export presets.

**Exit codes** suitable for CI.

---

## 11) Configuration & Profiles

`~/.sealimg/config.yml`

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
```

---

## 12) Repository Layout

```
sealimg/
  README.md
  LICENSE
  CHANGELOG.md
  /docs/
    overview.md
    quickstart.md
    cli.md
    config.md
    manifest.md
    file-formats.md
    cryptography.md
    roadmap.md
    faq.md
  /design/
    ux-flows.md
    wireframes.md
    data-models.md
    test-plan.md
  /specs/
    c2pa-notes.md
    iptc-xmp-mapping.md
    invisible-watermark-rationale.md
  /examples/
    sample-manifest.json
    sample-readme.txt
```

---

## 13) Documentation Plan (what each doc covers)

* **overview.md** — problem, goals, trust model.
* **quickstart.md** — install, seal one image, verify it.
* **cli.md** — commands, flags, examples.
* **config.md** — config file, profiles, defaults.
* **manifest.md** — schema with field descriptions.
* **file-formats.md** — embed strategies & fallbacks.
* **cryptography.md** — key management, signing, verification.
* **roadmap.md** — milestones & future work.
* **faq.md** — “Do I need invisible watermark?”, “What if metadata is stripped?” etc.
* **c2pa-notes.md** — how manifests are embedded; links to spec.
* **iptc-xmp-mapping.md** — exact fields written (Author, Copyright, Web URL).
* **invisible-watermark-rationale.md** — pros/cons, robustness caveats.
* **test-plan.md** — how to validate sealing and verification across OS/viewers.

---

## 14) Testing Strategy

* **Golden fixtures:** small sample images with known manifests/signatures.
* **Cross-tool verification:** ensure output verifies with independent tools.
* **Mutation tests:** crop, resize, recompress—confirm signature still verifies (manifest is external) and embedded C2PA remains discoverable where supported.
* **Metadata stripping:** confirm fallback (sidecar manifest/ZIP) still proves origin.
* **Key rotation & revocation:** ensure verifier reports the correct status.

---

## 15) Security & Privacy Principles

* All operations are **local** by default; no network calls.
* Keys stored encrypted; passphrase never logged.
* Clear opt-in for any public timestamping/postbacks.
* Minimal PII in manifests (author name/URL only by default).

---

## 16) License & Governance

* **License:** Apache-2.0 or MIT (your call).
* **Contribution:** standard PRs + CLA-free.
* **Code of Conduct:** Contributor Covenant.
* **Versioning:** SemVer; pin manifest schema as `v1` until a breaking change.

---

## 17) Integrations & Ecosystem

* **SmileCMS plugin:** show “Provenance” badge if manifest present; link to JSON and/or bundle.
* **WordPress plugin (later):** verify on upload; surface a small badge on the media page.
* **CI usage:** `sealimg verify` step fails builds if assets are unsealed.

---

## 18) Risks & Mitigations

* **Invisible watermark robustness:** clearly documented as “deterrence, not guarantee”.
* **Browser support for C2PA display:** uneven; provide human-readable link + badge now.
* **Key loss:** strong “backup your key + revocation file” messaging.

---

## 19) Success Metrics (practical)

* Seal one image in <10 seconds locally.
* Zero config runs with good defaults.
* Verify sealed images with third-party tools.
* Artists report “I forgot about it—it just works.”

---

## 20) Roadmap (milestones)

* **v0.1**: PNG/JPEG seal & verify; SHA-256; IPTC/XMP; signed manifest; simple profiles.
* **v0.3**: C2PA embed for PNG/JPEG (where libs allow); provenance ZIP; watch/batch mode.
* **v0.5**: Invisible watermark optional; public timestamp hook.
* **v0.7**: AVIF/HEIC; per-recipient fingerprinting; pHash output.
* **v1.0**: GUI; docs polished; SmileCMS integration guide; WordPress proof-of-concept.

---

## 21) Glossary (for future you)

* **C2PA**: Open standard for signed provenance manifests inside media files.
* **JUMBF**: A container format for embedding structured data inside images.
* **IPTC/XMP**: Common metadata fields (author, copyright, URL).
* **SHA-256**: Cryptographic hash; unique fingerprint of a file.
* **Ed25519/RSA**: Algorithms to sign/verify data with keypairs.
* **pHash**: Perceptual hash for “looks like” detection.

---

If you want, I can also draft the initial `README.md` and stub the `/docs` files with headings you can flesh out later.
