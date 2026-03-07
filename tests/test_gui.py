from sealimg import gui


def test_build_seal_cli_args_includes_expected_flags() -> None:
    args = gui.build_seal_cli_args(
        paths=["img1.jpg", "folder"],
        recursive=True,
        profile="web",
        wm_visible=True,
        wm_invisible=False,
        bundle=False,
        no_embed=True,
        recipient_id="recipient-1",
        output_root="./sealed",
        config_path="~/.sealimg/config.yml",
        passphrase="secret",
    )

    assert args == [
        "seal",
        "img1.jpg",
        "folder",
        "--recursive",
        "--profile",
        "web",
        "--wm-visible",
        "on",
        "--wm-invisible",
        "off",
        "--bundle",
        "off",
        "--no-embed",
        "--recipient-id",
        "recipient-1",
        "--output-root",
        "./sealed",
        "--config-path",
        "~/.sealimg/config.yml",
        "--passphrase",
        "secret",
        "--json",
    ]


def test_build_seal_cli_args_omits_empty_option_values() -> None:
    args = gui.build_seal_cli_args(
        paths=["img.jpg"],
        recursive=False,
        profile="  ",
        wm_visible=False,
        wm_invisible=True,
        bundle=True,
        no_embed=False,
        recipient_id=" ",
        output_root=" ",
        config_path=" ",
        passphrase=" ",
    )

    assert args == [
        "seal",
        "img.jpg",
        "--wm-visible",
        "off",
        "--wm-invisible",
        "on",
        "--bundle",
        "on",
        "--json",
    ]


def test_extract_last_json_object_returns_payload_only_for_json_objects() -> None:
    assert gui.extract_last_json_object('line1\n{"ok": true, "count": 3}') == {
        "ok": True,
        "count": 3,
    }
    assert gui.extract_last_json_object("line1\nnot-json") is None
    assert gui.extract_last_json_object('line1\n["x"]') is None
    assert gui.extract_last_json_object("") is None


def test_gui_main_dispatches_to_run_gui(monkeypatch) -> None:
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
        return 9

    monkeypatch.setattr(gui, "run_gui", fake_run_gui)

    rc = gui.main(
        [
            "--config-path",
            "/tmp/cfg.yml",
            "--profile",
            "web",
            "--output-root",
            "/tmp/out",
        ]
    )

    assert rc == 9
    assert calls == {
        "config_path": "/tmp/cfg.yml",
        "default_profile": "web",
        "default_output_root": "/tmp/out",
    }
