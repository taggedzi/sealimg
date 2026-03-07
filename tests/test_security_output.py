from pathlib import Path

from sealimg import cli
from sealimg.crypto import KeyInfo, KeyPairPaths


def test_keygen_error_redacts_passphrase(monkeypatch, capsys) -> None:
    secret = "my-secret-pass"

    def boom(**_: object) -> object:
        raise cli.CryptoError(f"bad key setup with secret={secret}")

    monkeypatch.setattr(cli, "generate_keypair", boom)
    rc = cli.main(
        [
            "keygen",
            "--ed25519",
            "--name",
            "Tester",
            "--key-name",
            "tester",
            "--output-dir",
            ".",
            "--passphrase",
            secret,
        ]
    )
    out = capsys.readouterr().out
    assert rc == 1
    assert secret not in out
    assert "<redacted>" in out


def test_env_secret_is_redacted_in_error_output(monkeypatch, capsys) -> None:
    secret = "env-pass-123"
    monkeypatch.setenv("SEALIMG_PASSPHRASE", secret)

    def boom(**_: object) -> object:
        raise cli.CryptoError(f"env leak {secret}")

    monkeypatch.setattr(cli, "generate_keypair", boom)
    rc = cli.main(
        [
            "keygen",
            "--ed25519",
            "--name",
            "Tester",
            "--key-name",
            "tester",
            "--output-dir",
            ".",
        ]
    )
    out = capsys.readouterr().out
    assert rc == 1
    assert secret not in out
    assert "<redacted>" in out


def test_keygen_hides_private_key_path_by_default(monkeypatch, capsys) -> None:
    def fake_keygen(**_: object) -> KeyInfo:
        return KeyInfo(
            algorithm="ed25519",
            signer="Tester",
            fingerprint="abcd1234",
            paths=KeyPairPaths(
                private_key=Path("/tmp/private.key"),
                public_key=Path("/tmp/public.pub"),
            ),
        )

    monkeypatch.setattr(cli, "generate_keypair", fake_keygen)
    rc = cli.main(
        [
            "keygen",
            "--ed25519",
            "--name",
            "Tester",
            "--key-name",
            "tester",
            "--output-dir",
            ".",
            "--passphrase",
            "abc",
        ]
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert "Private key:" not in out
    assert "Public key:" in out


def test_keygen_verbose_shows_private_key_path(monkeypatch, capsys) -> None:
    def fake_keygen(**_: object) -> KeyInfo:
        return KeyInfo(
            algorithm="ed25519",
            signer="Tester",
            fingerprint="abcd1234",
            paths=KeyPairPaths(
                private_key=Path("/tmp/private.key"),
                public_key=Path("/tmp/public.pub"),
            ),
        )

    monkeypatch.setattr(cli, "generate_keypair", fake_keygen)
    rc = cli.main(
        [
            "keygen",
            "--ed25519",
            "--name",
            "Tester",
            "--key-name",
            "tester",
            "--output-dir",
            ".",
            "--passphrase",
            "abc",
            "--verbose",
        ]
    )
    out = capsys.readouterr().out
    assert rc == 0
    assert "Private key:" in out


def test_seal_error_redacts_passphrase(monkeypatch, capsys) -> None:
    secret = "seal-secret-777"

    cfg = cli._default_config()  # type: ignore[attr-defined]

    def fake_load(_: Path) -> object:
        return cfg

    def fake_paths(*_: object, **__: object) -> tuple[Path, Path]:
        return (Path("/tmp/key"), Path("/tmp/key.pub"))

    def fake_discover(*_: object, **__: object) -> list[Path]:
        return [Path("/tmp/image.png")]

    def fake_seal(*_: object, **__: object) -> object:
        raise RuntimeError(f"boom with {secret}")

    monkeypatch.setattr(cli, "_load_or_init_config", fake_load)
    monkeypatch.setattr(cli, "derive_paths_from_config", fake_paths)
    monkeypatch.setattr(cli, "discover_input_images", fake_discover)
    monkeypatch.setattr(cli, "seal_image", fake_seal)

    rc = cli.main(
        [
            "seal",
            "/tmp",
            "--config-path",
            "/tmp/does-not-matter.yml",
            "--passphrase",
            secret,
        ]
    )
    out = capsys.readouterr().out
    assert rc == 1
    assert secret not in out
    assert "<redacted>" in out
