from sealimg import cli


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
