from pathlib import Path

from PIL import Image

from sealimg.cli import main
from sealimg.timestamping import append_hash_line, build_hash_line


def _create_config_and_keys(tmp_path: Path) -> tuple[Path, Path, Path]:
    config_path = tmp_path / "config.yml"
    keys_dir = tmp_path / "keys"
    rc = main(
        [
            "keygen",
            "--ed25519",
            "--name",
            "Watcher",
            "--key-name",
            "watcher",
            "--output-dir",
            str(keys_dir),
            "--passphrase",
            "watch-pass",
        ]
    )
    assert rc == 0
    signing_key = keys_dir / "watcher_ed25519.key"
    public_key = keys_dir / "watcher_ed25519.pub"
    output_root = tmp_path / "sealed"
    rc = main(
        [
            "config",
            "set",
            "--author",
            "Watcher",
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
    return config_path, output_root, public_key


def test_watch_once_seals_new_files(tmp_path: Path) -> None:
    config_path, output_root, _ = _create_config_and_keys(tmp_path)
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir()
    Image.new("RGB", (640, 480), color=(22, 33, 44)).save(watch_dir / "new.png", format="PNG")

    rc = main(
        [
            "watch",
            str(watch_dir),
            "--once",
            "--config-path",
            str(config_path),
            "--passphrase",
            "watch-pass",
        ]
    )
    assert rc == 0
    assert any(p.is_dir() for p in output_root.iterdir())


def test_watch_once_writes_timestamp_log(tmp_path: Path) -> None:
    config_path, output_root, _ = _create_config_and_keys(tmp_path)
    watch_dir = tmp_path / "watch"
    watch_dir.mkdir()
    Image.new("RGB", (640, 480), color=(55, 44, 33)).save(watch_dir / "new2.png", format="PNG")
    ts_log = tmp_path / "hashes.txt"

    rc = main(
        [
            "watch",
            str(watch_dir),
            "--once",
            "--config-path",
            str(config_path),
            "--passphrase",
            "watch-pass",
            "--timestamp-log",
            str(ts_log),
        ]
    )
    assert rc == 0
    lines = ts_log.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) >= 1
    assert "IMG-" in lines[-1]

    sealed_dir = next(p for p in output_root.iterdir() if p.is_dir())
    manifest = sealed_dir / "manifest.json"
    line = build_hash_line(manifest, "IMG-TEST-LINE")
    append_hash_line(ts_log, line)
    assert "IMG-TEST-LINE" in ts_log.read_text(encoding="utf-8")
