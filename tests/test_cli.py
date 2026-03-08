import json
from pathlib import Path
from types import SimpleNamespace

import sealimg.cli as cli_module
from sealimg.c2pa import EmbedStatus
from sealimg.cli import main
from sealimg.crypto import public_key_fingerprint


def test_main_help_exits_successfully() -> None:
    rc = main([])
    assert rc == 0


def test_version_exits_successfully() -> None:
    try:
        main(["--version"])
    except SystemExit as exc:
        assert exc.code == 0


def test_key_show_fingerprint(tmp_path: Path, capsys) -> None:
    key = tmp_path / "sample.pub"
    key.write_text("-----BEGIN PUBLIC KEY-----\nabc\n-----END PUBLIC KEY-----\n", encoding="utf-8")

    rc = main(["key", "show", str(key), "--fingerprint"])
    out = capsys.readouterr().out.strip()
    assert rc == 0
    assert len(out) == 16


def test_key_show_missing_file_returns_error(capsys) -> None:
    rc = main(["key", "show", "missing.pub"])
    out = capsys.readouterr().out
    assert rc == 1
    assert "unable to read key file" in out


def test_gui_command_dispatches(monkeypatch) -> None:
    calls: dict[str, str | None] = {}

    def fake_run_gui(
        *,
        config_path: str,
        default_profile: str | None = None,
        default_output_root: str | None = None,
    ) -> int:
        calls["config_path"] = config_path
        calls["default_profile"] = default_profile
        calls["default_output_root"] = default_output_root
        return 7

    monkeypatch.setattr(cli_module, "run_gui", fake_run_gui)
    rc = main(
        [
            "gui",
            "--config-path",
            "/tmp/sealimg.yml",
            "--profile",
            "web",
            "--output-root",
            "/tmp/out",
        ]
    )
    assert rc == 7
    assert calls == {
        "config_path": "/tmp/sealimg.yml",
        "default_profile": "web",
        "default_output_root": "/tmp/out",
    }


def test_key_revoke_and_list(tmp_path: Path, capsys) -> None:
    revocations = tmp_path / "revocations.txt"
    rc = main(
        [
            "key",
            "revoke",
            "--fingerprint",
            "abc123",
            "--reason",
            "key compromise",
            "--date",
            "2026-03-07",
            "--revocations-file",
            str(revocations),
        ]
    )
    assert rc == 0

    rc = main(["key", "revocations", "list", "--revocations-file", str(revocations)])
    out = capsys.readouterr().out
    assert rc == 0
    assert "abc123 2026-03-07 key compromise" in out


def test_verify_strict_revocation_returns_code_2(tmp_path: Path, capsys, monkeypatch) -> None:
    pub = tmp_path / "sample.pub"
    pub.write_bytes(b"sample-public-key")
    fp = public_key_fingerprint(pub.read_bytes())
    revocations = tmp_path / "revocations.txt"
    revocations.write_text(f"{fp} 2026-03-07 key compromise\n", encoding="utf-8")

    monkeypatch.setattr(
        cli_module,
        "verify_target",
        lambda *_args, **_kwargs: SimpleNamespace(
            manifest_path=Path("manifest.json"),
            signature_valid=True,
            key_id_match=True,
            hash_valid=True,
            master_phash="0123456789abcdef",
            web_phash="fedcba9876543210",
            master_embed_status=EmbedStatus(status="none", message=""),
            web_embed_status=EmbedStatus(status="none", message=""),
            sidecar_available=True,
        ),
    )
    rc = main(
        [
            "verify",
            "manifest.json",
            "--pubkey",
            str(pub),
            "--revocations-file",
            str(revocations),
            "--strict-revocation",
            "--json",
        ]
    )
    payload = json.loads(capsys.readouterr().out)
    assert payload["revocation"]["key_revoked"] is True
    assert rc == 2
