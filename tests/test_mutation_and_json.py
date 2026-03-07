import json
from pathlib import Path

from PIL import Image
from PIL.PngImagePlugin import PngInfo

from sealimg.cli import main


def _setup_sealed_artifact(tmp_path: Path) -> tuple[Path, Path, Path]:
    config_path = tmp_path / "config.yml"
    image_path = tmp_path / "input.jpg"
    Image.new("RGB", (1000, 700), color=(100, 80, 40)).save(image_path, format="JPEG", quality=95)

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

    sealed_dir = next(p for p in output_root.iterdir() if p.is_dir())
    return sealed_dir, config_path, public_key


def test_verify_returns_code_2_on_modified_file(tmp_path: Path) -> None:
    sealed_dir, _, public_key = _setup_sealed_artifact(tmp_path)
    web_path = sealed_dir / "web.jpg"
    web_path.write_bytes(web_path.read_bytes() + b"tampered")

    rc = main(["verify", str(sealed_dir / "manifest.json"), "--pubkey", str(public_key)])
    assert rc == 2


def test_verify_returns_code_2_on_modified_manifest(tmp_path: Path) -> None:
    sealed_dir, _, public_key = _setup_sealed_artifact(tmp_path)
    manifest = sealed_dir / "manifest.json"
    updated = manifest.read_text(encoding="utf-8").replace("Tester", "Intruder")
    manifest.write_text(updated, encoding="utf-8")

    rc = main(["verify", str(manifest), "--pubkey", str(public_key)])
    assert rc == 2


def test_json_outputs_for_seal_verify_inspect(tmp_path: Path, capsys) -> None:
    sealed_dir, config_path, public_key = _setup_sealed_artifact(tmp_path)
    capsys.readouterr()
    image_path = tmp_path / "extra.png"
    Image.new("RGB", (800, 500), color=(20, 20, 20)).save(image_path, format="PNG")

    rc = main(
        [
            "seal",
            str(image_path),
            "--config-path",
            str(config_path),
            "--passphrase",
            "test-passphrase",
            "--json",
        ]
    )
    assert rc == 0
    seal_json = json.loads(capsys.readouterr().out)
    assert seal_json["ok"] is True
    assert seal_json["count"] == 1

    rc = main(
        [
            "verify",
            str(sealed_dir / "manifest.json"),
            "--pubkey",
            str(public_key),
            "--json",
        ]
    )
    assert rc == 0
    verify_json = json.loads(capsys.readouterr().out)
    assert verify_json["signature_valid"] is True
    assert verify_json["hash_valid"] is True

    rc = main(["inspect", str(sealed_dir / "web.jpg"), "--json"])
    assert rc == 0
    inspect_json = json.loads(capsys.readouterr().out)
    assert inspect_json["format"] == "jpeg"
    assert inspect_json["width"] > 0


def test_metadata_stripped_copy_does_not_break_sidecar_verification(tmp_path: Path) -> None:
    sealed_dir, _, public_key = _setup_sealed_artifact(tmp_path)
    web = sealed_dir / "web.jpg"
    stripped_copy = sealed_dir / "web-stripped.png"

    with Image.open(web) as image:
        image.save(stripped_copy, format="PNG", pnginfo=PngInfo())

    # Sidecar verification still succeeds for the original sealed package.
    rc = main(["verify", str(sealed_dir / "manifest.json"), "--pubkey", str(public_key)])
    assert rc == 0
