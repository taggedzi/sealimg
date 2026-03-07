import pytest

from sealimg.manifest import MANIFEST_SCHEMA_V1, ManifestError, ManifestV1


def _manifest_payload() -> dict:
    return {
        "schema": MANIFEST_SCHEMA_V1,
        "image_id": "IMG-2026-03-06-0001",
        "author": "Matthew Craig",
        "website": "https://taggedz.me",
        "license": "CC BY-NC 4.0",
        "files": {
            "master": {"path": "master.png", "sha256": "a" * 64},
            "web": {"path": "web.jpg", "sha256": "b" * 64},
        },
        "timestamps": {
            "local_created": "2026-03-06T15:01:01-05:00",
            "sealed_utc": "2026-03-06T20:01:02Z",
        },
        "signature": {
            "algo": "ed25519",
            "signer": "Matthew Craig",
            "pubkey_fingerprint": "ABC123",
            "signature_file": "manifest.sig",
        },
    }


def test_manifest_accepts_valid_payload() -> None:
    model = ManifestV1.from_dict(_manifest_payload())
    assert model.image_id == "IMG-2026-03-06-0001"


def test_manifest_rejects_unknown_field() -> None:
    payload = _manifest_payload()
    payload["extra"] = "nope"
    with pytest.raises(ManifestError):
        ManifestV1.from_dict(payload)


def test_manifest_rejects_invalid_timestamp() -> None:
    payload = _manifest_payload()
    payload["timestamps"]["sealed_utc"] = "not-a-date"
    with pytest.raises(ManifestError):
        ManifestV1.from_dict(payload)


def test_manifest_rejects_wrong_schema() -> None:
    payload = _manifest_payload()
    payload["schema"] = "https://example.com/v9"
    with pytest.raises(ManifestError):
        ManifestV1.from_dict(payload)
