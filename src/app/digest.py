"""
digest.py — Cryptographic Digest Helpers

Provides SHA-256 hashing utilities used by gossip nodes to produce deterministic
digests of their state payloads. Peers compare digests (alongside counters) during
the quorum consensus phase to guarantee they hold identical data before confirming
convergence.
"""

import json
import hashlib


def mk_digest(payload: dict) -> str:
    """
    Produce a deterministic SHA-256 hex digest of a nested dictionary.

    The dictionary is JSON-serialised with sorted keys before hashing to ensure
    that two nodes holding semantically identical state always produce the same
    digest regardless of insertion order.

    Args:
        payload: The gossip state dict to hash.

    Returns:
        A 64-character lowercase hex string (SHA-256 digest).
    """
    serialised = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(serialised.encode('utf-8')).hexdigest()
