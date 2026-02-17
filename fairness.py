from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass, field


@dataclass
class FairnessEngine:
    server_seed: str = field(default_factory=lambda: secrets.token_hex(32))
    user_nonces: dict[int, int] = field(default_factory=dict)

    @property
    def commit(self) -> str:
        return hashlib.sha256(self.server_seed.encode("utf-8")).hexdigest()

    def next_nonce(self, user_id: int) -> int:
        nonce = self.user_nonces.get(user_id, 0) + 1
        self.user_nonces[user_id] = nonce
        return nonce

    def current_nonce(self, user_id: int) -> int:
        return self.user_nonces.get(user_id, 0)

    def digest_for_spin(self, client_seed: str, nonce: int) -> str:
        message = f"{client_seed}:{nonce}".encode("utf-8")
        digest = hmac.new(self.server_seed.encode("utf-8"), message, hashlib.sha256).hexdigest()
        return digest

    @staticmethod
    def digest_to_unit_float(digest_hex: str) -> float:
        value = int(digest_hex[:16], 16)
        return value / float(1 << 64)

    def reveal_and_rotate_seed(self) -> tuple[str, str, str]:
        old_seed = self.server_seed
        old_commit = self.commit
        self.server_seed = secrets.token_hex(32)
        return old_seed, old_commit, self.commit
