"""Native cryptographic key/signature operations."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path


class CryptoError(RuntimeError):
    """Raised when crypto operations fail."""


def _require_cryptography():
    try:
        from cryptography.hazmat.primitives import hashes, serialization
        from cryptography.hazmat.primitives.asymmetric import ed25519, padding, rsa
        from cryptography.hazmat.primitives.serialization import (
            BestAvailableEncryption,
            NoEncryption,
            PrivateFormat,
            PublicFormat,
        )
    except Exception as exc:  # pragma: no cover - exercised in environments without deps
        raise CryptoError(
            "cryptography package is required for native key/signature features"
        ) from exc
    return {
        "hashes": hashes,
        "serialization": serialization,
        "ed25519": ed25519,
        "padding": padding,
        "rsa": rsa,
        "BestAvailableEncryption": BestAvailableEncryption,
        "NoEncryption": NoEncryption,
        "PrivateFormat": PrivateFormat,
        "PublicFormat": PublicFormat,
    }


@dataclass(frozen=True)
class KeyPairPaths:
    private_key: Path
    public_key: Path


@dataclass(frozen=True)
class KeyInfo:
    algorithm: str
    signer: str
    fingerprint: str
    paths: KeyPairPaths


def generate_keypair(
    output_dir: Path,
    signer: str,
    passphrase: str,
    algorithm: str = "ed25519",
    key_name: str = "sealimg",
) -> KeyInfo:
    c = _require_cryptography()
    output_dir.mkdir(parents=True, exist_ok=True)

    algo = algorithm.lower()
    if algo not in {"ed25519", "rsa"}:
        raise CryptoError("algorithm must be 'ed25519' or 'rsa'")

    if algo == "ed25519":
        private_key = c["ed25519"].Ed25519PrivateKey.generate()
    else:
        private_key = c["rsa"].generate_private_key(public_exponent=65537, key_size=3072)

    public_key = private_key.public_key()

    enc = c["BestAvailableEncryption"](passphrase.encode("utf-8"))
    private_pem = private_key.private_bytes(
        encoding=c["serialization"].Encoding.PEM,
        format=c["PrivateFormat"].PKCS8,
        encryption_algorithm=enc,
    )
    public_pem = public_key.public_bytes(
        encoding=c["serialization"].Encoding.PEM,
        format=c["PublicFormat"].SubjectPublicKeyInfo,
    )

    private_path = output_dir / f"{key_name}_{algo}.key"
    public_path = output_dir / f"{key_name}_{algo}.pub"
    private_path.write_bytes(private_pem)
    public_path.write_bytes(public_pem)

    fingerprint = public_key_fingerprint(public_pem)
    return KeyInfo(
        algorithm=algo,
        signer=signer,
        fingerprint=fingerprint,
        paths=KeyPairPaths(private_key=private_path, public_key=public_path),
    )


def public_key_fingerprint(public_key_pem: bytes) -> str:
    digest = hashlib.sha256(public_key_pem).hexdigest()
    return digest[:16]


def sign_bytes(payload: bytes, private_key_path: Path, passphrase: str) -> bytes:
    c = _require_cryptography()
    private_key = c["serialization"].load_pem_private_key(
        private_key_path.read_bytes(), password=passphrase.encode("utf-8")
    )

    if isinstance(private_key, c["ed25519"].Ed25519PrivateKey):
        return private_key.sign(payload)

    if isinstance(private_key, c["rsa"].RSAPrivateKey):
        return private_key.sign(
            payload,
            c["padding"].PSS(
                mgf=c["padding"].MGF1(c["hashes"].SHA256()),
                salt_length=c["padding"].PSS.MAX_LENGTH,
            ),
            c["hashes"].SHA256(),
        )

    raise CryptoError("Unsupported private key type")


def verify_bytes(payload: bytes, signature: bytes, public_key_path: Path) -> bool:
    c = _require_cryptography()
    public_key = c["serialization"].load_pem_public_key(public_key_path.read_bytes())

    try:
        if isinstance(public_key, c["ed25519"].Ed25519PublicKey):
            public_key.verify(signature, payload)
            return True
        if isinstance(public_key, c["rsa"].RSAPublicKey):
            public_key.verify(
                signature,
                payload,
                c["padding"].PSS(
                    mgf=c["padding"].MGF1(c["hashes"].SHA256()),
                    salt_length=c["padding"].PSS.MAX_LENGTH,
                ),
                c["hashes"].SHA256(),
            )
            return True
    except Exception:
        return False

    raise CryptoError("Unsupported public key type")


def sign_file(
    input_path: Path,
    signature_path: Path,
    private_key_path: Path,
    passphrase: str,
) -> None:
    signature = sign_bytes(input_path.read_bytes(), private_key_path, passphrase)
    signature_path.write_bytes(signature)


def verify_file(input_path: Path, signature_path: Path, public_key_path: Path) -> bool:
    return verify_bytes(input_path.read_bytes(), signature_path.read_bytes(), public_key_path)
