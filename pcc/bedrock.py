from __future__ import annotations
import time, uuid
from dataclasses import dataclass, asdict
from typing import List, Dict, Any, Tuple
from .canonical import canonical_json
from .merkle import merkle_root
from .version import VERSION, GIT_SHA, DECISION_SCHEMA_VERSION
ISO_FMT = "%Y-%m-%dT%H:%M:%SZ"
@dataclass
class Check:
    token: str
    ok: bool
    details: str | None = None
    source: str | None = None
def utc_now_iso() -> str:
    return time.strftime(ISO_FMT, time.gmtime())
def build_decision(tool: str, asset_id: str, token: str, decision: str, posture: str, checks: List[Check], pack: str | None = None, registry_sha: str | None = None) -> Dict[str, Any]:
    assert decision in ("allow", "block")
    assert posture in ("advice", "enforce")
    if decision == "allow":
        exit_code = 0
        reason = "allow because ok, window 5m"
    else:
        exit_code = 2 if posture == "enforce" else 1
        reason = f"blocked because {token}, held 5m"
    record = {
        "tool": tool,
        "tool_version": VERSION,
        "git_sha": GIT_SHA,
        "decision_schema_version": DECISION_SCHEMA_VERSION,
        "asset_id": asset_id,
        "token": token,
        "decision": decision,
        "reason": reason,
        "window": "5m",
        "exit_code": exit_code,
        "ts": utc_now_iso(),
        "correlation_id": str(uuid.uuid4()),
        "posture": posture,
        "checks": [asdict(c) for c in checks][:32]
    }
    if pack: record["pack"] = pack
    if registry_sha: record["registry_sha"] = registry_sha
    return record
def write_receipts_and_root(receipts_path: str, root_path: str, rows: List[dict]) -> str:
    def key(r: dict) -> Tuple:
        return (r.get("asset_id",""), r.get("token",""), r.get("ts",""), r.get("type",""))
    sorted_rows = sorted(rows, key=key)
    with open(receipts_path, "wb") as f:
        for r in sorted_rows:
            f.write(canonical_json(r))
    with open(receipts_path, "rb") as f:
        lines = f.read().splitlines(keepends=True)
    root = merkle_root(lines)
    with open(root_path, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"root: {root}\n")
        f.write(f"lines: {len(lines)}\n")
        f.write(f"ts: {utc_now_iso()}\n")
        f.write(f"tool_version: {VERSION}\n")
        f.write(f"git_sha: {GIT_SHA}\n")
    return root
