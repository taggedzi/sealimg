from pathlib import Path

from sealimg import gui
from sealimg.config import SealimgConfig, save_config


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

    cfg2 = SealimgConfig.from_dict(
        {
            "author": "Matthew Craig",
            "website": "https://example.com",
            "license": "CC BY-NC 4.0",
            "default_profile": "web",
            "output_root": "./sealed",
            "signing_key": str(tmp_path / "keys" / "sealimg_ed25519.key"),
            "profiles": {"web": {"long_edge": 2560, "jpeg_quality": 82}},
        }
    )
    save_config(cfg_path, cfg2)
    assert gui.infer_default_signer_name(str(cfg_path)) == "Matthew Craig"


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
