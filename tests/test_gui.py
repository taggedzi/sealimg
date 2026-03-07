from pathlib import Path

from sealimg import gui
from sealimg.config import SealimgConfig, load_config, save_config


def test_has_tkinterdnd2_reflects_find_spec(monkeypatch) -> None:
    monkeypatch.setattr(gui.importlib.util, "find_spec", lambda _name: object())
    assert gui.has_tkinterdnd2() is True

    monkeypatch.setattr(gui.importlib.util, "find_spec", lambda _name: None)
    assert gui.has_tkinterdnd2() is False


def test_build_seal_cli_args_includes_expected_flags() -> None:
    args = gui.build_seal_cli_args(
        paths=["img1.jpg", "folder"],
        recursive=True,
        profile="web",
        wm_visible=True,
        wm_invisible=False,
        wm_invisible_mode="auto",
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
        "--wm-invisible-mode",
        "auto",
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
        wm_invisible_mode="owner",
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
        "--wm-invisible-mode",
        "owner",
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


def test_parse_dropped_paths_handles_braced_and_plain_items() -> None:
    data = "{C:/Users/me/Pictures/with space.jpg} C:/tmp/plain.png {C:/tmp/dir one}"
    assert gui.parse_dropped_paths(data) == [
        "C:/Users/me/Pictures/with space.jpg",
        "C:/tmp/plain.png",
        "C:/tmp/dir one",
    ]


def test_parse_dropped_paths_handles_empty_input() -> None:
    assert gui.parse_dropped_paths("") == []
    assert gui.parse_dropped_paths("   ") == []


def test_resolve_config_dialog_start_dir_prefers_current_parent(tmp_path: Path) -> None:
    cfg = tmp_path / "nested" / "config.yml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    out = gui.resolve_config_dialog_start_dir(str(cfg), "~/.sealimg/config.yml")
    assert out == str(cfg.parent)


def test_resolve_config_dialog_start_dir_falls_back_to_default_parent(tmp_path: Path) -> None:
    default_cfg = tmp_path / ".sealimg" / "config.yml"
    default_cfg.parent.mkdir(parents=True, exist_ok=True)
    out = gui.resolve_config_dialog_start_dir(
        str(tmp_path / "missing" / "path" / "config.yml"),
        str(default_cfg),
    )
    assert out == str(default_cfg.parent)


def test_resolve_output_root_dialog_start_dir_prefers_existing_dir(tmp_path: Path) -> None:
    out_dir = tmp_path / "sealed"
    out_dir.mkdir(parents=True, exist_ok=True)
    out = gui.resolve_output_root_dialog_start_dir(str(out_dir), None)
    assert out == str(out_dir)


def test_resolve_output_root_dialog_start_dir_falls_back_to_default(tmp_path: Path) -> None:
    default_out = tmp_path / "default-out"
    default_out.mkdir(parents=True, exist_ok=True)
    out = gui.resolve_output_root_dialog_start_dir(
        str(tmp_path / "missing" / "nested" / "sealed"),
        str(default_out),
    )
    assert out == str(default_out)


def test_select_profile_name_prefers_web_when_available() -> None:
    assert gui.select_profile_name(["print", "web"], requested=None) == "web"
    assert gui.select_profile_name(["print", "web"], requested="print") == "print"
    assert gui.select_profile_name(["print"], requested=None) == "print"


def test_derive_profile_watermark_state_defaults() -> None:
    state = gui.derive_profile_watermark_state(None)
    assert state["visible_enabled"] is True
    assert state["invisible_enabled"] is False
    assert state["invisible_mode"] == "auto"


def test_derive_profile_watermark_state_from_profile_values() -> None:
    state = gui.derive_profile_watermark_state(
        {
            "wm_visible": {"enabled": False, "style": "flat", "text": "© tester"},
            "wm_invisible": {"enabled": True, "mode": "owner"},
        }
    )
    assert state["visible_enabled"] is False
    assert state["visible_style"] == "flat"
    assert state["visible_text"] == "© tester"
    assert state["invisible_enabled"] is True
    assert state["invisible_mode"] == "owner"


def test_load_profile_choices_defaults_to_web_when_config_missing(tmp_path: Path) -> None:
    names, selected = gui.load_profile_choices(str(tmp_path / "missing.yml"), requested=None)
    assert names == ["web"]
    assert selected == "web"


def test_profile_upsert_and_delete_helpers(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.yml"
    cfg = SealimgConfig.from_dict(
        {
            "author": "Tester",
            "website": "https://example.com",
            "license": "CC BY-NC 4.0",
            "default_profile": "web",
            "output_root": "./sealed",
            "signing_key": str(tmp_path / "keys" / "sealimg_ed25519.key"),
            "profiles": {"web": {"long_edge": 2560, "jpeg_quality": 82}},
        }
    )
    save_config(cfg_path, cfg)

    gui.upsert_profile_in_config(
        str(cfg_path),
        profile_name="print",
        long_edge=6000,
        quality=95,
        wm_visible_enabled=False,
        wm_invisible_enabled=True,
        wm_invisible_mode="owner",
        wm_style="diag-low",
        wm_text="",
        make_default=True,
    )
    updated = load_config(cfg_path)
    assert "print" in updated.profiles
    assert updated.default_profile == "print"
    assert updated.profiles["print"]["wm_invisible"]["mode"] == "owner"

    new_default = gui.delete_profile_from_config(str(cfg_path), "print")
    updated2 = load_config(cfg_path)
    assert new_default == "web"
    assert updated2.default_profile == "web"
    assert "print" not in updated2.profiles


def test_detect_bootstrap_needs_missing_config(tmp_path: Path) -> None:
    has_keys, invalid = gui.detect_bootstrap_needs(str(tmp_path / "missing.yml"))
    assert has_keys is False
    assert invalid is False


def test_detect_bootstrap_needs_invalid_config(tmp_path: Path) -> None:
    cfg_path = tmp_path / "config.yml"
    cfg_path.write_text("not: [valid", encoding="utf-8")
    has_keys, invalid = gui.detect_bootstrap_needs(str(cfg_path))
    assert has_keys is False
    assert invalid is True


def test_detect_bootstrap_needs_key_presence(tmp_path: Path) -> None:
    key_path = tmp_path / "keys" / "sealimg_ed25519.key"
    cfg = SealimgConfig.from_dict(
        {
            "author": "Tester",
            "website": "https://example.com",
            "license": "CC BY-NC 4.0",
            "default_profile": "web",
            "output_root": "./sealed",
            "signing_key": str(key_path),
            "profiles": {"web": {"long_edge": 2560, "jpeg_quality": 82}},
        }
    )
    cfg_path = tmp_path / "config.yml"
    save_config(cfg_path, cfg)

    has_keys, invalid = gui.detect_bootstrap_needs(str(cfg_path))
    assert has_keys is False
    assert invalid is False

    key_path.parent.mkdir(parents=True, exist_ok=True)
    key_path.write_text("priv", encoding="utf-8")
    key_path.with_suffix(".pub").write_text("pub", encoding="utf-8")

    has_keys, invalid = gui.detect_bootstrap_needs(str(cfg_path))
    assert has_keys is True
    assert invalid is False


def test_infer_default_signer_name(tmp_path: Path) -> None:
    missing = gui.infer_default_signer_name(str(tmp_path / "missing.yml"))
    assert missing == "sealimg"

    cfg_path = tmp_path / "config.yml"
    cfg = SealimgConfig.from_dict(
        {
            "author": "Your Name",
            "website": "https://example.com",
            "license": "CC BY-NC 4.0",
            "default_profile": "web",
            "output_root": "./sealed",
            "signing_key": str(tmp_path / "keys" / "sealimg_ed25519.key"),
            "profiles": {"web": {"long_edge": 2560, "jpeg_quality": 82}},
        }
    )
    save_config(cfg_path, cfg)
    assert gui.infer_default_signer_name(str(cfg_path)) == "sealimg"


def test_collect_about_info_includes_expected_fields(tmp_path: Path) -> None:
    info = gui.collect_about_info(str(tmp_path / "config.yml"))
    assert info["Sealimg version"]
    assert info["Python version"]
    assert info["Platform"]
    assert info["OS"]
    assert info["Executable"]
    assert info["TkinterDnD2"] in {"installed", "not installed"}
    assert str(tmp_path / "config.yml") in info["Config path"]


def test_build_keygen_cli_args_uses_config_sibling_keys_dir(tmp_path: Path) -> None:
    cfg_path = tmp_path / ".sealimg" / "config.yml"
    args = gui.build_keygen_cli_args(
        config_path=str(cfg_path),
        passphrase="secret",
        signer_name="Signer",
    )
    assert args == [
        "keygen",
        "--ed25519",
        "--name",
        "Signer",
        "--key-name",
        "sealimg",
        "--output-dir",
        str(cfg_path.parent / "keys"),
        "--passphrase",
        "secret",
        "--config-path",
        str(cfg_path),
        "--write-config",
    ]


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
