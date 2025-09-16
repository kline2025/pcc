from __future__ import annotations
import json
def canonical_json(obj) -> bytes:
    s = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    if not s.endswith("\n"):
        s += "\n"
    return s.encode("utf-8")
