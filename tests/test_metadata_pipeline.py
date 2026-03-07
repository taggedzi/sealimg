import importlib.util
from hashlib import sha256
from pathlib import Path

import pytest

from sealimg.image_pipeline import (
    WebExportOptions,
    create_master_copy,
    create_web_copy,
    detect_format,
)
from sealimg.metadata import XMP_HEADER, MetadataFields, build_xmp_packet

PIL_AVAILABLE = importlib.util.find_spec("PIL") is not None

pytestmark = pytest.mark.skipif(not PIL_AVAILABLE, reason="Pillow is not installed")


def _sample_metadata() -> MetadataFields:
    return MetadataFields(
        author="Matthew Craig",
        website="https://taggedz.me",
        license="CC BY-NC 4.0",
        copyright_notice="(c) Matthew Craig",
        title="Test Piece",
        description="Metadata pipeline test",
    )


def _make_source_images(tmp_path: Path) -> tuple[Path, Path]:
    from PIL import Image

    png_path = tmp_path / "input.png"
    jpg_path = tmp_path / "input.jpg"
    Image.new("RGB", (1600, 900), color=(40, 80, 120)).save(png_path, format="PNG")
    Image.new("RGB", (1800, 1000), color=(20, 30, 70)).save(jpg_path, format="JPEG", quality=95)
    return png_path, jpg_path


def test_build_xmp_packet_contains_expected_fields() -> None:
    packet = build_xmp_packet(_sample_metadata())
    assert b"dc:creator" in packet
    assert b"Iptc4xmpExt:WebStatement" in packet
    assert b"xmpRights:UsageTerms" in packet


def test_xmp_packet_matches_iptc_xmp_mapping_spec() -> None:
    packet = build_xmp_packet(_sample_metadata())
    # Mapping coverage from specs/iptc-xmp-mapping.md
    assert b"Iptc4xmpExt:WebStatement" in packet
    assert b"dcterms:identifier" in packet
    assert b"dc:creator" in packet
    assert b"dc:rights" in packet
    assert b"xmpRights:Marked" in packet
    assert b"xmpRights:UsageTerms" in packet
    assert b"dc:description" in packet
    assert b"dc:title" in packet


def test_create_master_copy_png_and_jpeg_embeds_xmp(tmp_path: Path) -> None:
    png_in, jpg_in = _make_source_images(tmp_path)
    fields = _sample_metadata()

    png_master = tmp_path / "master.png"
    jpg_master = tmp_path / "master.jpg"
    create_master_copy(png_in, png_master, fields)
    create_master_copy(jpg_in, jpg_master, fields)

    png_data = png_master.read_bytes()
    jpg_data = jpg_master.read_bytes()
    assert b"XML:com.adobe.xmp" in png_data
    assert XMP_HEADER in jpg_data


def test_web_export_resizes_and_embeds_metadata(tmp_path: Path) -> None:
    png_in, _ = _make_source_images(tmp_path)
    web_out = tmp_path / "web.jpg"
    create_web_copy(
        input_path=png_in,
        output_path=web_out,
        metadata_fields=_sample_metadata(),
        options=WebExportOptions(
            long_edge=800,
            jpeg_quality=82,
            visible_watermark_enabled=True,
            visible_watermark_text="(c) Matthew Craig",
            visible_watermark_style="diag-low",
        ),
    )

    from PIL import Image

    with Image.open(web_out) as image:
        assert max(image.size) == 800
    assert XMP_HEADER in web_out.read_bytes()


def test_invisible_watermark_provider_is_called(tmp_path: Path) -> None:
    png_in, _ = _make_source_images(tmp_path)
    web_out = tmp_path / "web-inv.jpg"

    class DummyProvider:
        called = False

        def apply(self, image: object, payload: str) -> object:
            self.called = True
            return image

    provider = DummyProvider()
    create_web_copy(
        input_path=png_in,
        output_path=web_out,
        metadata_fields=_sample_metadata(),
        options=WebExportOptions(
            long_edge=900,
            visible_watermark_enabled=False,
            invisible_watermark_enabled=True,
            invisible_watermark_payload="IMG-2026-03-06-0001",
        ),
        invisible_provider=provider,
    )
    assert provider.called is True


def test_default_invisible_watermark_changes_output(tmp_path: Path) -> None:
    from PIL import Image

    png_in = tmp_path / "input-textured.png"
    textured = Image.new("RGB", (320, 200))
    textured.putdata(
        [
            (
                (x * 13 + y * 7) % 256,
                (x * 5 + y * 11) % 256,
                (x * 17 + y * 3) % 256,
            )
            for y in range(200)
            for x in range(320)
        ]
    )
    textured.save(png_in, format="PNG")
    plain_out = tmp_path / "web-plain.jpg"
    inv_out = tmp_path / "web-inv-default.jpg"

    create_web_copy(
        input_path=png_in,
        output_path=plain_out,
        metadata_fields=_sample_metadata(),
        options=WebExportOptions(
            long_edge=900,
            visible_watermark_enabled=False,
            invisible_watermark_enabled=False,
        ),
    )
    create_web_copy(
        input_path=png_in,
        output_path=inv_out,
        metadata_fields=_sample_metadata(),
        options=WebExportOptions(
            long_edge=900,
            visible_watermark_enabled=False,
            invisible_watermark_enabled=True,
            invisible_watermark_payload="IMG-2026-03-07-0001",
        ),
    )

    assert sha256(plain_out.read_bytes()).hexdigest() != sha256(inv_out.read_bytes()).hexdigest()


def test_detect_format_for_png_and_jpeg(tmp_path: Path) -> None:
    png_in, jpg_in = _make_source_images(tmp_path)
    assert detect_format(png_in) == "png"
    assert detect_format(jpg_in) == "jpeg"


def test_detect_format_supports_v07_extensions(tmp_path: Path) -> None:
    avif = tmp_path / "sample.avif"
    heic = tmp_path / "sample.heic"
    heif = tmp_path / "sample.heif"
    jxl = tmp_path / "sample.jxl"
    for p in (avif, heic, heif, jxl):
        p.write_bytes(b"not-real-image")

    assert detect_format(avif) == "avif"
    assert detect_format(heic) == "heic"
    assert detect_format(heif) == "heic"
    assert detect_format(jxl) == "jxl"


def test_master_copy_passthrough_for_v07_formats(tmp_path: Path) -> None:
    source = tmp_path / "sample.avif"
    source.write_bytes(b"avif-bytes-placeholder")
    out = tmp_path / "master.avif"

    create_master_copy(source, out, _sample_metadata())
    assert out.read_bytes() == source.read_bytes()
