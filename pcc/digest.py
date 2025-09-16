from __future__ import annotations
import sys, os, json, time
from typing import List, Dict
from .bedrock import build_decision, write_receipts_and_root, Check
from .ingest import iter_zip_members
TOOL = "tender-digest"
PACK = "tender-core"
def _asset_id_from(zip_path: str, kind: str) -> str:
    base = os.path.basename(zip_path).replace(".zip", "")
    base = base.replace(" ", "_").lower()
    return f"tender:{kind}/{base}"
def record_ts():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
def main(argv: List[str] | None = None) -> int:
    import argparse
    ap = argparse.ArgumentParser(prog="pcc-digest", description="PCC — Procurement Coherence & Compliance (digest)")
    ap.add_argument("--tender-zip", required=True, help="Path to buyer tender ZIP")
    ap.add_argument("--offer-zip", required=False, help="Path to bidder offer ZIP")
    ap.add_argument("--out", required=True, help="Output directory")
    ap.add_argument("--posture", choices=["advice","enforce"], default="advice", help="Effective posture")
    ap.add_argument("--registry-sha", default=None, help="Optional registry etag/sha string")
    args = ap.parse_args(argv)
    os.makedirs(args.out, exist_ok=True)
    receipts_path = os.path.join(args.out, "proof", "receipts.jsonl")
    root_path = os.path.join(args.out, "proof", "root.txt")
    os.makedirs(os.path.dirname(receipts_path), exist_ok=True)
    rows: List[Dict] = []
    checks: List[Check] = []
    try:
        tender_members = iter_zip_members(args.tender_zip)
    except Exception as e:
        record = build_decision(TOOL, _asset_id_from(args.tender_zip, "pack"), token="system:parse_error", decision="block", posture=args.posture, checks=[Check(token="system:parse_error", ok=False, details=str(e))], pack=PACK, registry_sha=args.registry_sha)
        print(json.dumps(record, ensure_ascii=False))
        print(record["reason"], file=sys.stderr)
        return record["exit_code"]
    rows.append({"type":"system","asset_id":_asset_id_from(args.tender_zip, "pack"),"token":"tender:pack:parse_ok","parse_ok":True,"docs":len(tender_members),"ocr_pages":0,"ts":record_ts()})
    checks.append(Check(token="tender:pack:parse_ok", ok=True, details=f"docs={len(tender_members)}; allowed={sum(1 for m in tender_members if m['allowed'])}"))
    offer_members = []
    if args.offer_zip:
        try:
            offer_members = iter_zip_members(args.offer_zip)
            rows.append({"type":"system","asset_id":_asset_id_from(args.offer_zip, "offer"),"token":"tender:pack:parse_ok","parse_ok":True,"docs":len(offer_members),"ocr_pages":0,"ts":record_ts()})
        except Exception as e:
            record = build_decision(TOOL, _asset_id_from(args.offer_zip, "offer"), token="system:parse_error", decision="block", posture=args.posture, checks=[Check(token="system:parse_error", ok=False, details=str(e))], pack=PACK, registry_sha=args.registry_sha)
            print(json.dumps(record, ensure_ascii=False))
            print(record["reason"], file=sys.stderr)
            return record["exit_code"]
    checks.extend([Check(token="tender:criteria:weights_disclosed", ok=False, details="not_implemented"),Check(token="tender:criteria:formula_disclosed", ok=False, details="not_implemented"),Check(token="tender:coherence:notice_itt_consistent", ok=False, details="not_implemented")])
    total_size = sum(m["size"] for m in tender_members) + sum(m["size"] for m in offer_members)
    rows.append({"type":"summary","asset_id":_asset_id_from(args.tender_zip, "pack"),"docs_total": len(tender_members) + len(offer_members),"bytes_total": total_size, "ts": record_ts()})
    write_receipts_and_root(receipts_path, root_path, rows)
    asset_id = _asset_id_from(args.offer_zip or args.tender_zip, "offer" if args.offer_zip else "pack")
    record = build_decision(TOOL, asset_id, token="ok", decision="allow", posture=args.posture, checks=checks, pack=PACK, registry_sha=args.registry_sha)
    print(json.dumps(record, ensure_ascii=False))
    print(record["reason"], file=sys.stderr)
    return record["exit_code"]
if __name__ == "__main__":
    raise SystemExit(main())
