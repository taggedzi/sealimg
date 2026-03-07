import json
from pathlib import Path

from sealimg.crypto import generate_keypair
from sealimg.ids import ImageIdGenerator
from sealimg.metadata import MetadataFields
from sealimg.workflow import seal_image


def _canonicalize_manifest(path: Path) -> dict:
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["timestamps"]["local_created"] = "<timestamp>"
    payload["timestamps"]["sealed_utc"] = "<timestamp>"
    payload["files"]["master"]["sha256"] = "<sha256>"
    payload["files"]["web"]["sha256"] = "<sha256>"
    payload["signature"]["pubkey_fingerprint"] = "<fingerprint>"
    return payload


def test_manifest_matches_golden_snapshot(tmp_path: Path) -> None:
    fixture = Path("tests/fixtures/images/mj-1/0096b6ad-14bf-4559-941f-fa02c8fc4583.png")
    assert fixture.exists()

    key_info = generate_keypair(
        output_dir=tmp_path / "keys",
        signer="Tester",
        passphrase="test-passphrase",
        algorithm="ed25519",
        key_name="snapshot",
    )

    result = seal_image(
        input_path=fixture,
        output_root=tmp_path / "sealed",
        id_generator=ImageIdGenerator(prefix="IMG"),
        metadata=MetadataFields(
            author="Tester",
            website="https://example.test",
            license="CC BY-NC 4.0",
            copyright_notice="(c) Tester",
        ),
        profile_defaults={},
        selected_profile={
            "long_edge": 2560,
            "jpeg_quality": 82,
            "wm_visible": {"enabled": True, "text": "© Tester • example.test", "style": "diag-low"},
            "wm_invisible": {"enabled": False},
        },
        cli_overrides={},
        bundle=False,
        embed_enabled=True,
        signing_key_path=key_info.paths.private_key,
        passphrase="test-passphrase",
        signer_name="Tester",
        public_key_path=key_info.paths.public_key,
        image_id_override="IMG-TEST-0001",
    )

    expected = json.loads(
        Path("tests/fixtures/golden/manifest-v1.snapshot.json").read_text("utf-8")
    )
    actual = _canonicalize_manifest(result.manifest_path)
    assert actual == expected
