from pathlib import Path

from PIL import Image

from sealimg.cli import main
from sealimg.workflow import discover_input_images


def test_discover_input_images_handles_nested_and_non_ascii_names(tmp_path: Path) -> None:
    base = tmp_path / "gallery space"
    nested = base / "子目录"
    nested.mkdir(parents=True)
    img1 = base / "plain-name.png"
    img2 = nested / "näme-测试.jpg"
    Image.new("RGB", (100, 80), color=(1, 2, 3)).save(img1, format="PNG")
    Image.new("RGB", (120, 90), color=(3, 2, 1)).save(img2, format="JPEG")

    non_recursive = discover_input_images([base], recursive=False)
    recursive = discover_input_images([base], recursive=True)

    assert img1 in non_recursive
    assert img2 not in non_recursive
    assert img1 in recursive
    assert img2 in recursive


def test_seal_supports_non_ascii_input_filename(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yml"
    image_path = tmp_path / "艺术作品.png"
    Image.new("RGB", (900, 600), color=(10, 20, 30)).save(image_path, format="PNG")

    keys_dir = tmp_path / "keys"
    rc = main(
        [
            "keygen",
            "--ed25519",
            "--name",
            "Tester",
            "--key-name",
            "tester",
            "--output-dir",
            str(keys_dir),
            "--passphrase",
            "test-passphrase",
        ]
    )
    assert rc == 0

    signing_key = keys_dir / "tester_ed25519.key"
    output_root = tmp_path / "sealed"
    rc = main(
        [
            "config",
            "set",
            "--author",
            "Tester",
            "--site",
            "https://example.test",
            "--license",
            "CC BY-NC 4.0",
            "--output-root",
            str(output_root),
            "--default-profile",
            "web",
            "--signing-key",
            str(signing_key),
            "--config-path",
            str(config_path),
        ]
    )
    assert rc == 0

    rc = main(
        [
            "seal",
            str(image_path),
            "--config-path",
            str(config_path),
            "--passphrase",
            "test-passphrase",
        ]
    )
    assert rc == 0
    assert any(p.is_dir() for p in output_root.iterdir())
