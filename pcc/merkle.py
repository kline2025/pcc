from __future__ import annotations
import hashlib
from typing import Iterable
def merkle_root(lines: Iterable[bytes]) -> str:
    nodes = [hashlib.sha256(line).digest() for line in lines]
    if not nodes:
        return hashlib.sha256(b"").hexdigest()
    while len(nodes) > 1:
        nxt = []
        it = iter(nodes)
        for a in it:
            try:
                b = next(it)
            except StopIteration:
                b = a
            nxt.append(hashlib.sha256(a + b).digest())
        nodes = nxt
    return nodes[0].hex()
