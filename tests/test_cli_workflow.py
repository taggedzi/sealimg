from pathlib import Path

from PIL import Image

from sealimg.cli import main


def test_config_and_profile_commands(tmp_path: Path, capsys) -> None:
    config_path = tmp_path / "config.yml"

    rc = main(["config", "get", "--config-path", str(config_path)])
    assert rc == 0

    rc = main(
        [
            "profile",
            "add",
            "portfolio",
            "--long-edge",
            "1920",
            "--quality",
            "85",
            "--wm-visible",
            "on",
            "--wm-text",
            "demo",
            "--config-path",
            str(config_path),
        ]
    )
    assert rc == 0

    rc = main(["profile", "list", "--config-path", str(config_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "portfolio" in out

    rc = main(["profile", "show", "portfolio", "--config-path", str(config_path)])
    out = capsys.readouterr().out
    assert rc == 0
    assert 'jpeg_quality: 85' in out


def test_seal_verify_and_inspect_flow(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yml"
    image_path = tmp_path / "input.png"
    Image.new("RGB", (1200, 800), color=(44, 66, 88)).save(image_path, format="PNG")

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
    public_key = keys_dir / "tester_ed25519.pub"
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
            "--bundle",
            "on",
            "--config-path",
            str(config_path),
            "--passphrase",
            "test-passphrase",
        ]
    )
    assert rc == 0

    sealed_dirs = [p for p in output_root.iterdir() if p.is_dir()]
    assert len(sealed_dirs) == 1
    sealed_dir = sealed_dirs[0]
    manifest = sealed_dir / "manifest.json"
    web_image = sealed_dir / "web.jpg"
    assert manifest.exists()
    assert (sealed_dir / "manifest.sig").exists()
    assert (sealed_dir / "sha256.txt").exists()
    assert (sealed_dir / "README.txt").exists()
    assert (sealed_dir / "provenance.zip").exists()

    rc = main(["verify", str(manifest), "--pubkey", str(public_key)])
    assert rc == 0

    rc = main(["inspect", str(web_image)])
    assert rc == 0
