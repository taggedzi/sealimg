import json
from pathlib import Path

from PIL import Image
from PIL.PngImagePlugin import PngInfo

from sealimg import workflow
from sealimg.c2pa import EmbedStatus
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
    seal_result = seal_json["results"][0]
    assert seal_result["embed"]["master"]["status"] == "embedded"
    assert seal_result["embed"]["web"]["status"] == "embedded"
    assert seal_result["sidecar"]["available"] is True

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
    assert verify_json["key_id_match"] is True
    assert verify_json["hash_valid"] is True
    assert verify_json["embed"]["master"]["status"] == "detected"
    assert verify_json["embed"]["web"]["status"] == "detected"
    assert verify_json["sidecar"]["available"] is True

    rc = main(["inspect", str(sealed_dir / "web.jpg"), "--json"])
    assert rc == 0
    inspect_json = json.loads(capsys.readouterr().out)
    assert inspect_json["format"] == "jpeg"
    assert inspect_json["width"] > 0
    assert inspect_json["embed"]["master"]["status"] == "detected"
    assert inspect_json["embed"]["web"]["status"] == "detected"
    assert inspect_json["sidecar"]["available"] is True


def test_metadata_stripped_copy_does_not_break_sidecar_verification(tmp_path: Path) -> None:
    sealed_dir, _, public_key = _setup_sealed_artifact(tmp_path)
    web = sealed_dir / "web.jpg"
    stripped_png = sealed_dir / "web-stripped.png"
    stripped_jpg = sealed_dir / "web-stripped.jpg"

    with Image.open(web) as image:
        image.save(stripped_png, format="PNG", pnginfo=PngInfo())
        image.save(stripped_jpg, format="JPEG", quality=85)

    # Sidecar verification still succeeds for the original sealed package.
    rc = main(["verify", str(sealed_dir / "manifest.json"), "--pubkey", str(public_key)])
    assert rc == 0


def test_verify_fails_when_pubkey_does_not_match_manifest_key_id(tmp_path: Path, capsys) -> None:
    sealed_dir, _, _ = _setup_sealed_artifact(tmp_path)
    capsys.readouterr()
    other_keys = tmp_path / "other-keys"
    rc = main(
        [
            "keygen",
            "--ed25519",
            "--name",
            "Other",
            "--key-name",
            "other",
            "--output-dir",
            str(other_keys),
            "--passphrase",
            "test-passphrase",
        ]
    )
    assert rc == 0
    capsys.readouterr()
    other_pub = other_keys / "other_ed25519.pub"
    rc = main(
        [
            "verify",
            str(sealed_dir / "manifest.json"),
            "--pubkey",
            str(other_pub),
            "--json",
        ]
    )
    assert rc == 2
    out = json.loads(capsys.readouterr().out)
    assert out["key_id_match"] is False


def test_seal_json_reports_mixed_embed_outcomes(tmp_path: Path, capsys, monkeypatch) -> None:
    sealed_dir, config_path, _ = _setup_sealed_artifact(tmp_path)
    capsys.readouterr()
    image_path = tmp_path / "mixed.png"
    Image.new("RGB", (500, 320), color=(10, 30, 50)).save(image_path, format="PNG")

    def fake_attempt_embed(image_path: Path, *_: object, **__: object) -> EmbedStatus:
        if image_path.name.startswith("master"):
            return EmbedStatus(status="embedded", message="master embed ok")
        return EmbedStatus(status="failed", message="web fallback to sidecar")

    monkeypatch.setattr(workflow, "attempt_embed_claim", fake_attempt_embed)
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
    out = json.loads(capsys.readouterr().out)
    result = out["results"][0]
    assert result["embed"]["master"]["status"] == "embedded"
    assert result["embed"]["web"]["status"] == "failed"
    assert result["sidecar"]["available"] is True
    assert (sealed_dir.parent).exists()


def test_verify_json_reports_mixed_detected_states(tmp_path: Path, capsys, monkeypatch) -> None:
    sealed_dir, _, public_key = _setup_sealed_artifact(tmp_path)
    capsys.readouterr()

    def fake_inspect(path: Path) -> EmbedStatus:
        if path.name.startswith("master"):
            return EmbedStatus(status="detected", message="master marker present")
        return EmbedStatus(status="none", message="web marker absent")

    monkeypatch.setattr(workflow, "inspect_embed_status", fake_inspect)
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
    out = json.loads(capsys.readouterr().out)
    assert out["embed"]["master"]["status"] == "detected"
    assert out["embed"]["web"]["status"] == "none"
    assert out["sidecar"]["available"] is True
