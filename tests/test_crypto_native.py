import importlib.util

import pytest

from sealimg.crypto import generate_keypair, sign_bytes, verify_bytes

pytestmark = pytest.mark.skipif(
    importlib.util.find_spec("cryptography") is None,
    reason="cryptography dependency is not installed",
)


@pytest.mark.parametrize("algorithm", ["ed25519", "rsa"])
def test_sign_and_verify_round_trip(tmp_path, algorithm: str) -> None:
    info = generate_keypair(
        output_dir=tmp_path / "keys",
        signer="Tester",
        passphrase="test-passphrase",
        algorithm=algorithm,
        key_name="tester",
    )
    payload = b'{"schema":"https://sealimg.org/provenance/v1"}'
    signature = sign_bytes(payload, info.paths.private_key, "test-passphrase")

    assert verify_bytes(payload, signature, info.paths.public_key) is True
    assert verify_bytes(payload + b"x", signature, info.paths.public_key) is False
