from __future__ import annotations

import io
import logging
from collections.abc import Callable, Mapping
from dataclasses import dataclass, field
from os import urandom
from threading import Thread
from typing import Any
from socket import socket, AF_INET, SOCK_STREAM
from sys import argv
from time import sleep

from adaptix import P, dumper, loader
from cryptography.hazmat.primitives.asymmetric import ed25519  # Ed25519PrivateKey, Ed25519PublicKey

from microchat.entities import InviteAccept, PrivKey, Identity
from microchat.entities import ConferenceEvent, ConferenceStart, Invite, MessageEvent
from microchat.entities import SignedEventContainer
from microchat import serialization

from microchat.app import Storage, Client, Conference, Connection
from microchat.app import log
from microchat.app.crypto import Ed25519PrivateKey, Ed25519PublicKey, pubkey_dump, pubkey_load, privkey_load
from microchat.hashing import Reference


_retort = serialization._retort.extend(recipe=[
    dumper(P[Identity].pubkey, pubkey_dump),
    loader(P[Identity].pubkey, pubkey_load),
])
_codec = serialization.Codec(_retort)


@dataclass
class Actor:
    storage: Storage
    private_key: PrivKey
    event_callblack: Callable[[ConferenceEvent], Any] = (lambda event: None)
    client: Client = field(init=False)

    def __post_init__(self):
        self.client = Client(storage=self.storage, signing_key=self.private_key, event_callblack=self.event_callblack)

    @property
    def identity(self) -> Identity:
        return Identity(self.private_key.public_key)


def recv_exact(sock: socket, size: int) -> bytes:
    expected_length = size

    with io.BytesIO() as buffer:
        while expected_length > 0:
            recvd = sock.recv(expected_length)
            if not recvd:
                logging.warning("Connection dropped")
                break
            buffer.write(recvd)
            expected_length -= len(recvd)

        return buffer.getvalue()


class SocketConnection(Thread, Connection):
    def __init__(self, sock: socket, client: Client) -> None:
        super().__init__(name=f"<Thread {type(self).__name__}>")
        self._sock = sock
        self._client = client

    def send(self, event: SignedEventContainer) -> None:
        raw = _codec.dump(event)
        legth = len(raw)
        raw = legth.to_bytes(4, byteorder='big', signed=False) + raw
        self._sock.send(raw)

    def run(self) -> None:
        while True:
            length_raw = recv_exact(sock=self._sock, size=4)
            length = int.from_bytes(length_raw, byteorder='big', signed=False)
            payload = recv_exact(sock=self._sock, size=length)
            event = _codec.load(payload)
            if not isinstance(event, SignedEventContainer):
                logging.warning(f"Неизвестная хуйня типа {type(event).__name__}")
                continue
            self._client.dispatch(event)


def init_socket_connection(client: Client, sock: socket, self_key: PrivKey) -> tuple[Identity, SocketConnection]:
    # -> PubKey
    self_pub_bytes = self_key.public_key.raw
    log.info("Send pubkey (%s)", self_key.public_key)
    sock.send(self_pub_bytes)

    # <- PeerPubKey
    peer_pub_bytes = sock.recv(len(self_pub_bytes))
    peer_pub = Ed25519PublicKey(_key=ed25519.Ed25519PublicKey.from_public_bytes(peer_pub_bytes))
    log.info("Pubkey received: %s", peer_pub)

    CHALLENGE_LENGTH = 16
    CHALLENGE_SOLVE_LENGTH = 64

    # -> challenge_data
    challenge_data = urandom(CHALLENGE_LENGTH)
    log.info("Send challenge data")
    sock.send(challenge_data)

    # <- peer_challenge_data
    peer_challenge_data = sock.recv(CHALLENGE_LENGTH)
    log.info("Peer challenge data received")

    # -> challenge_solve
    challenge_solve = self_key.sign(peer_challenge_data)
    log.info("Send challenge solve")
    sock.send(challenge_solve)

    # <- peer_challenge_solve
    peer_challenge_solve = sock.recv(CHALLENGE_SOLVE_LENGTH)
    log.info("Peer challenge solve received")
    peer_pub.verify(signature=peer_challenge_solve, data=challenge_data)

    connection = SocketConnection(sock=sock, client=client)
    connection.start()
    return Identity(pubkey=peer_pub), connection


class ClentNetworking:
    def __init__(self, privkey: PrivKey, client: Client) -> None:
        self._privkey = privkey
        self._peers: dict[Reference[Identity], Connection] = {}
        self._client = client

    @property
    def peers(self) -> Mapping[Reference[Identity], Connection]:
        return self._peers

    def connect(self, address: str, port: int) -> None:
        sock = socket(AF_INET, SOCK_STREAM)
        sock.connect((address, port))

        peer_identity, connection = init_socket_connection(
            self._client,
            sock=sock,
            self_key=self._privkey
        )
        self._peers[peer_identity.reference()] = connection


class ServerNetworking(Thread):
    def __init__(self, host: str, port: int, privkey: PrivKey, client: Client) -> None:
        super().__init__(name=f"<Thread {type(self).__name__} on {privkey}>")
        self._privkey = privkey
        self._client = client
        self._addr = (host, port)
        self._sock: socket | None = None
        self._peers: dict[Reference[Identity], Connection] = {}

    @property
    def peers(self) -> Mapping[Reference[Identity], Connection]:
        return self._peers

    def run(self) -> None:
        if self._sock:
            raise RuntimeError
        self._sock = socket(AF_INET, SOCK_STREAM)
        self._sock.bind(self._addr)
        self._sock.listen()

        while True:
            sock, (remote_host, remote_port) = self._sock.accept()
            logging.info(f"New connection from {remote_host} ({remote_port})")
            peer_identity, connection = init_socket_connection(
                self._client,
                sock=sock,
                self_key=self._privkey
            )
            self._peers[peer_identity.reference()] = connection


def example():
    creator = Actor(Storage(), Ed25519PrivateKey())
    member = Actor(Storage(), Ed25519PrivateKey())

    conference = creator.client.create_conference("amogus")
    invite = conference.invite(member.identity)
    member_conference = member.client.accept_invite(invite)

    conference.send_message(text="first")
    member_conference.send_message(text="second")


def main(argv: list[str]) -> None:
    HOST = "localhost"
    PORT = 1011

    client_key = privkey_load('d6cd9ebf05c1446f199cb96f14e003d91cef4178718bb548e2890190757d8e85')
    server_key = privkey_load('784bb6ff6c8b56c3c3555d03f53c7de18a4a572a9358240d53307f8f51dfb23d')

    match argv:
        case [_] | [_, "client"]:
            client_main(host=HOST, port=PORT, private_key=client_key)
        case [_, "server"]:
            server_main(host=HOST, port=PORT, private_key=server_key)


def client_main(host: str, port: int, private_key: Ed25519PrivateKey) -> None:
    storage = Storage()
    actor = Actor(storage=storage, private_key=private_key)
    network = ClentNetworking(privkey=private_key, client=actor.client)
    network.connect(host, port)

    while True:
        sleep(0.1)


def server_main(host: str, port: int, private_key: Ed25519PrivateKey) -> None:
    conferences: dict[Reference[ConferenceStart], Conference] = {}

    def on_event(event: ConferenceEvent) -> None:
        match event:
            case Invite():
                conference = actor.client.accept_invite(event)
                conferences[conference._start_ref] = conference
            case MessageEvent():
                acceptance = storage.resolve(event.conference_acceptance)
                if isinstance(acceptance, InviteAccept):
                    invite = storage.resolve(acceptance.invite)
                    conference = conferences[invite.conference]
                else:
                    conference = conferences[acceptance.reference()]

    storage = Storage()
    actor = Actor(storage=storage, private_key=private_key, event_callblack=on_event)
    network = ServerNetworking(host=host, port=port, privkey=private_key, client=actor.client)
    network.start()

    while True:
        sleep(0.1)


if __name__ == "__main__":
    log_formatter = logging.Formatter('[%(asctime)s] %(levelname)s (%(name)s): %(message)s')
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    console_handler.setFormatter(log_formatter)
    log.addHandler(console_handler)
    log.setLevel(logging.DEBUG)

    main(argv)
