import zipfile
from pathlib import Path

from sealimg.artifacts import (
    PackageReadmeContext,
    compute_sha256_map,
    create_provenance_zip,
    render_package_readme,
    sha256_file,
    sign_manifest,
    update_manifest_file_hashes,
    write_manifest,
    write_package_readme,
    write_sha256_file,
)
from sealimg.crypto import generate_keypair, verify_file
from sealimg.manifest import MANIFEST_SCHEMA_V1, ManifestV1


def _sample_manifest() -> ManifestV1:
    return ManifestV1.from_dict(
        {
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
    )


def test_sha256_and_sha256_txt(tmp_path: Path) -> None:
    master = tmp_path / "master.png"
    web = tmp_path / "web.jpg"
    master.write_bytes(b"master-bytes")
    web.write_bytes(b"web-bytes")

    assert len(sha256_file(master)) == 64
    out = tmp_path / "sha256.txt"
    write_sha256_file(out, {"web": web, "master": master})
    lines = out.read_text(encoding="utf-8").strip().splitlines()
    assert lines[0].endswith("master.png")
    assert lines[1].endswith("web.jpg")
    hmap = compute_sha256_map({"master": master, "web": web})
    assert set(hmap.keys()) == {"master", "web"}
    assert all(len(v) == 64 for v in hmap.values())


def test_update_manifest_file_hashes(tmp_path: Path) -> None:
    master = tmp_path / "master.png"
    web = tmp_path / "web.jpg"
    master.write_bytes(b"m")
    web.write_bytes(b"w")

    updated = update_manifest_file_hashes(
        {"schema": MANIFEST_SCHEMA_V1, "files": {}},
        master_path=master,
        web_path=web,
    )
    assert updated["files"]["master"]["path"] == "master.png"
    assert len(updated["files"]["master"]["sha256"]) == 64
    assert updated["files"]["web"]["path"] == "web.jpg"
    assert len(updated["files"]["web"]["sha256"]) == 64


def test_manifest_write_sign_and_verify(tmp_path: Path) -> None:
    manifest = _sample_manifest()
    manifest_path = tmp_path / "manifest.json"
    sig_path = tmp_path / "manifest.sig"

    write_manifest(manifest_path, manifest)
    text = manifest_path.read_text(encoding="utf-8")
    assert '"author": "Matthew Craig"' in text

    key_info = generate_keypair(
        output_dir=tmp_path / "keys",
        signer="Matthew Craig",
        passphrase="test-passphrase",
        algorithm="ed25519",
        key_name="tester",
    )
    sign_manifest(manifest_path, sig_path, key_info.paths.private_key, "test-passphrase")
    assert verify_file(manifest_path, sig_path, key_info.paths.public_key) is True


def test_package_readme_generation_and_write(tmp_path: Path) -> None:
    ctx = PackageReadmeContext(
        image_id="IMG-2026-03-06-0001",
        author="Matthew Craig",
        website="https://taggedz.me",
        license="CC BY-NC 4.0",
        master_filename="master.png",
        web_filename="web.jpg",
    )
    readme = render_package_readme(ctx)
    assert "SEALIMG - SEALED ARTWORK PACKAGE" in readme
    assert "Image ID: IMG-2026-03-06-0001" in readme

    out = tmp_path / "README.txt"
    write_package_readme(out, ctx)
    assert out.read_text(encoding="utf-8") == readme


def test_create_provenance_zip_contains_expected_files(tmp_path: Path) -> None:
    master = tmp_path / "master.png"
    web = tmp_path / "web.jpg"
    manifest = tmp_path / "manifest.json"
    sig = tmp_path / "manifest.sig"
    hashes = tmp_path / "sha256.txt"
    readme = tmp_path / "README.txt"
    for p in (master, web, manifest, sig, hashes, readme):
        p.write_text(p.name, encoding="utf-8")

    zip_path = tmp_path / "provenance.zip"
    create_provenance_zip(zip_path, [master, web, manifest, sig, hashes, readme])

    with zipfile.ZipFile(zip_path, "r") as zf:
        names = sorted(zf.namelist())
    assert names == [
        "README.txt",
        "manifest.json",
        "manifest.sig",
        "master.png",
        "sha256.txt",
        "web.jpg",
    ]
