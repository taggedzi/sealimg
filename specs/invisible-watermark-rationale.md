# Invisible Watermark — Rationale & Caveats

## Why
- Acts as a deterrent and a forensic clue linking a file to an image_id/signature without altering the visible image.

## Reality Check
- Robust but not invulnerable. Heavy edits (crop, blur, AI inpainting) can degrade/remove signals.
- Treat as *supplementary*, not primary proof (that’s the signed manifest).

## Payload
- Minimal: `image_id` + short signature tag or hash prefix.
- Avoid PII; keep payload small.

## Policy
- Off by default in "web" profile; on in "print" profile (optional).
