from pathlib import Path

import sealimg.cli as cli_module
from sealimg.cli import main


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
