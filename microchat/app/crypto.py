from dataclasses import dataclass, field

from cryptography.hazmat.primitives.asymmetric import ed25519

from microchat.entities import PrivKey, PubKey


@dataclass(frozen=True)
class Ed25519PrivateKey(PrivKey):
    _key: ed25519.Ed25519PrivateKey = field(default_factory=ed25519.Ed25519PrivateKey.generate)

    @property
    def public_key(self) -> PubKey:
        return Ed25519PublicKey(self._key.public_key())

    def sign(self, data: bytes) -> bytes:
        return self._key.sign(data)


@dataclass(frozen=True)
class Ed25519PublicKey(PubKey):
    _key: ed25519.Ed25519PublicKey

    @property
    def raw(self) -> bytes:
        return self._key.public_bytes_raw()

    def verify(self, data: bytes, signature: bytes) -> None:
        return self._key.verify(signature, data)


def pubkey_dump(pubkey: PubKey) -> str:
    return pubkey.raw.hex()


def pubkey_load(string: str) -> PubKey:
    key_bytes = bytes.fromhex(string)
    key = ed25519.Ed25519PublicKey.from_public_bytes(key_bytes)
    return Ed25519PublicKey(key)


def privkey_dump(privkey: Ed25519PrivateKey) -> str:
    return privkey._key.private_bytes_raw().hex()


def privkey_load(string: str) -> Ed25519PrivateKey:
    key_bytes = bytes.fromhex(string)
    key = ed25519.Ed25519PrivateKey.from_private_bytes(key_bytes)
    return Ed25519PrivateKey(key)
