from pathlib import Path

from PIL import Image, ImageEnhance

from sealimg.phash import compute_phash


def _make_image(path: Path) -> None:
    image = Image.new("RGB", (256, 256))
    image.putdata(
        [
            (
                (x * 9 + y * 5) % 256,
                (x * 7 + y * 13) % 256,
                (x * 3 + y * 11) % 256,
            )
            for y in range(256)
            for x in range(256)
        ]
    )
    image.save(path, format="PNG")


def test_phash_is_deterministic(tmp_path: Path) -> None:
    path = tmp_path / "img.png"
    _make_image(path)
    first = compute_phash(path)
    second = compute_phash(path)
    assert first == second
    assert len(first) == 16


def test_phash_changes_for_modified_image(tmp_path: Path) -> None:
    source = tmp_path / "img.png"
    edited = tmp_path / "img-edited.png"
    _make_image(source)

    with Image.open(source) as image:
        adjusted = ImageEnhance.Brightness(image).enhance(1.2)
        adjusted.save(edited, format="PNG")

    assert compute_phash(source) != compute_phash(edited)
