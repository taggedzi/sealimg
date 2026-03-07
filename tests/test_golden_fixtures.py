from pathlib import Path

from sealimg.artifacts import sha256_file


def test_mj1_source_images_match_golden_hashes() -> None:
    root = Path("tests/fixtures/images/mj-1")
    golden = Path("tests/fixtures/golden/mj-1-source-sha256.txt")
    assert root.exists(), "Fixture directory missing"
    assert golden.exists(), "Golden hash file missing"

    expected: dict[str, str] = {}
    for line in golden.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        hash_value, filename = line.split("  ", 1)
        expected[filename] = hash_value

    actual_files = sorted(p for p in root.iterdir() if p.is_file())
    assert len(actual_files) == len(expected), "Fixture file count drifted from golden snapshot"

    for image_path in actual_files:
        assert image_path.name in expected, f"Unexpected fixture file: {image_path.name}"
        assert sha256_file(image_path) == expected[image_path.name], (
            f"Hash mismatch: {image_path.name}"
        )
