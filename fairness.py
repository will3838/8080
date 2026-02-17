from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from typing import Dict


@dataclass
class SpinProof:
    nonce: int
    client_seed: str
    r: float


class FairnessEngine:
    def __init__(self) -> None:
        self.server_seed = self._new_seed()
        self.commit = self._commit(self.server_seed)
        self._nonces: Dict[int, int] = {}

    @staticmethod
    def _new_seed() -> str:
        return secrets.token_hex(32)

    @staticmethod
    def _commit(seed: str) -> str:
        return hashlib.sha256(seed.encode("utf-8")).hexdigest()

    def current_nonce(self, user_id: int) -> int:
        return self._nonces.get(user_id, 0)

    def next_spin(self, user_id: int, chat_id: int, message_id: int) -> SpinProof:
        nonce = self._nonces.get(user_id, 0) + 1
        self._nonces[user_id] = nonce
        client_seed = f"{user_id}:{chat_id}:{message_id}"
        payload = f"{client_seed}:{nonce}".encode("utf-8")
        digest = hmac.new(self.server_seed.encode("utf-8"), payload, hashlib.sha256).digest()
        value = int.from_bytes(digest[:8], "big")
        r = value / float(1 << 64)
        return SpinProof(nonce=nonce, client_seed=client_seed, r=r)

    def reveal_and_rotate(self) -> tuple[str, str]:
        old_seed = self.server_seed
        self.server_seed = self._new_seed()
        self.commit = self._commit(self.server_seed)
        return old_seed, self.commit
