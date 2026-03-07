from pathlib import Path

import pytest

from sealimg.config import ConfigError, SealimgConfig, load_config, save_config


def _sample_config_dict() -> dict:
    return {
        "author": "Matthew Craig",
        "website": "https://taggedz.me",
        "license": "CC BY-NC 4.0",
        "default_profile": "web",
        "output_root": "./sealed",
        "signing_key": "~/.sealimg/keys/matt.key",
        "profiles": {
            "web": {
                "long_edge": 2560,
                "jpeg_quality": 82,
                "wm_visible": {"enabled": True, "text": "x"},
            },
            "print": {"long_edge": 6000, "jpeg_quality": 95},
        },
    }


def test_config_from_dict_validates_required_fields() -> None:
    data = _sample_config_dict()
    config = SealimgConfig.from_dict(data)
    assert config.default_profile == "web"


def test_config_from_dict_rejects_missing_key() -> None:
    data = _sample_config_dict()
    data.pop("author")
    with pytest.raises(ConfigError):
        SealimgConfig.from_dict(data)


def test_config_requires_default_profile_to_exist() -> None:
    data = _sample_config_dict()
    data["default_profile"] = "missing"
    with pytest.raises(ConfigError):
        SealimgConfig.from_dict(data)


def test_config_roundtrip_yaml(tmp_path: Path) -> None:
    config = SealimgConfig.from_dict(_sample_config_dict())
    path = tmp_path / "config.yml"
    save_config(path, config)
    loaded = load_config(path)
    assert loaded == config
