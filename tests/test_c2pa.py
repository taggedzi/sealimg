from pathlib import Path

from PIL import Image

from sealimg.c2pa import attempt_embed_claim, inspect_embed_status


def _create_images(tmp_path: Path) -> tuple[Path, Path, Path]:
    jpg = tmp_path / "img.jpg"
    png = tmp_path / "img.png"
    manifest = tmp_path / "manifest.json"
    Image.new("RGB", (400, 300), color=(12, 34, 56)).save(jpg, format="JPEG")
    Image.new("RGB", (400, 300), color=(56, 34, 12)).save(png, format="PNG")
    manifest.write_text('{"schema":"https://sealimg.org/provenance/v1"}\n', encoding="utf-8")
    return jpg, png, manifest


def test_embed_and_detect_for_jpeg_and_png(tmp_path: Path) -> None:
    jpg, png, manifest = _create_images(tmp_path)
    assert inspect_embed_status(jpg).status == "none"
    assert inspect_embed_status(png).status == "none"

    jpg_status = attempt_embed_claim(jpg, manifest, enabled=True)
    png_status = attempt_embed_claim(png, manifest, enabled=True)
    assert jpg_status.status == "embedded"
    assert png_status.status == "embedded"

    assert inspect_embed_status(jpg).status == "detected"
    assert inspect_embed_status(png).status == "detected"


def test_embed_is_idempotent_for_jpeg_and_png(tmp_path: Path) -> None:
    jpg, png, manifest = _create_images(tmp_path)
    assert attempt_embed_claim(jpg, manifest, enabled=True).status == "embedded"
    assert attempt_embed_claim(jpg, manifest, enabled=True).status == "embedded"
    assert inspect_embed_status(jpg).status == "detected"

    assert attempt_embed_claim(png, manifest, enabled=True).status == "embedded"
    assert attempt_embed_claim(png, manifest, enabled=True).status == "embedded"
    assert inspect_embed_status(png).status == "detected"


def test_embed_skipped_when_disabled(tmp_path: Path) -> None:
    jpg, _, manifest = _create_images(tmp_path)
    status = attempt_embed_claim(jpg, manifest, enabled=False)
    assert status.status == "skipped"
    assert inspect_embed_status(jpg).status == "none"


def test_embed_reports_unsupported_for_non_png_jpeg(tmp_path: Path) -> None:
    manifest = tmp_path / "manifest.json"
    target = tmp_path / "asset.webp"
    manifest.write_text('{"schema":"https://sealimg.org/provenance/v1"}\n', encoding="utf-8")
    target.write_bytes(b"not-a-real-webp")
    status = attempt_embed_claim(target, manifest, enabled=True)
    assert status.status == "unsupported"
