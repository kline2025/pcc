from __future__ import annotations
import sys, os, json, time, re, zipfile
from typing import List, Dict
from .bedrock import build_decision, write_receipts_and_root, Check
from .ingest import iter_zip_members
from .requirements import extract_requirements, map_offer
from .offer_checks import detect_prohibited_conditions, check_format_ok
from .matrix import write_matrices
from .price_check import validate_prices
from .addenda import parse_addenda

TOOL = "tender-digest"
PACK = "tender-core"

ENFORCED_TOKENS = {
    "tender:pack:parse_ok",
    "tender:req:mandatories_all_present",
    "tender:offer:prohibited_conditions_absent",
    "tender:offer:format_ok",
    "tender:price:arithmetic_ok"
}

def _asset_id_from(zip_path: str, kind: str) -> str:
    base = os.path.basename(zip_path).replace(".zip", "")
    base = base.replace(" ", "_").lower()
    return f"tender:{kind}/{base}"

def record_ts():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

def extract_weights(zip_path: str) -> Dict:
    lines, files = [], []
    with zipfile.ZipFile(zip_path, "r") as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            name = info.filename
            ext = os.path.splitext(name)[1].lower()
            if ext not in {".txt", ".csv"}:
                continue
            text = z.read(info).decode("utf-8", errors="ignore")
            for line in text.splitlines():
                if "weight" in line.lower():
                    lines.append(line.strip()); files.append(name)
    nums = []
    for line in lines:
        nums += [float(x) for x in re.findall(r"\b\d+(?:\.\d+)?\b", line)]
    total = sum(nums); found = bool(nums)
    return {"found": found, "total": total, "count": len(nums), "files": sorted(set(files)), "sample_lines": lines[:3], "source": "tender"}

def extract_formula(zip_path: str) -> Dict:
    hits, files = [], set()
    with zipfile.ZipFile(zip_path, "r") as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            name = info.filename
            ext = os.path.splitext(name)[1].lower()
            if ext not in {".txt", ".csv"}:
                continue
            text = z.read(info).decode("utf-8", errors="ignore")
            for line in text.splitlines():
                s = line.strip(); low = s.lower()
                if any(k in low for k in ["price", "pmin", "pmax", "lowest price"]) and any(sym in s for sym in ["=", "/", "*"]):
                    if any(k in low for k in ["score", "points", "normalized"]):
                        hits.append(s); files.add(name)
    return {"found": bool(hits), "files": sorted(files), "sample_lines": hits[:3]}

def parse_notice_itt(zip_path: str) -> Dict[str, Dict[str, str | None]]:
    data = {"notice": {"procedure": None, "lots": None}, "itt": {"procedure": None, "lots": None}}
    with zipfile.ZipFile(zip_path, "r") as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            name = info.filename.lower()
            ext = os.path.splitext(name)[1].lower()
            if ext not in {".txt", ".csv"}:
                continue
            text = z.read(info).decode("utf-8", errors="ignore")
            proc = None; lots = None
            m = re.search(r"procedure\s*:\s*([^\n\r]+)", text, re.IGNORECASE)
            if m: proc = m.group(1).strip()
            m = re.search(r"lots?\s*:\s*([0-9]+)", text, re.IGNORECASE)
            if m: lots = m.group(1).strip()
            if "notice" in name:
                if proc: data["notice"]["procedure"] = proc
                if lots: data["notice"]["lots"] = lots
            if "itt" in name or "invitation" in name or "tender" in name:
                if proc: data["itt"]["procedure"] = proc
                if lots: data["itt"]["lots"] = lots
    ok = True
    for field in ["procedure", "lots"]:
        n = data["notice"][field]; i = data["itt"][field]
        if n is not None and i is not None and n != i:
            ok = False
    data["ok"] = ok
    return data

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

    addn = parse_addenda(args.tender_zip)
    addenda_limit = addn["overrides"].get("word_limit") if addn["found"] else None
    w = extract_weights(args.tender_zip)
    if addn["found"] and "weights" in addn["overrides"]:
        w = {"found": True, "total": round(addn["overrides"]["weights"]["price"] + addn["overrides"]["weights"]["quality"], 2), "count": 2, "files": addn["files"], "sample_lines": [f"Weights: Price {addn['overrides']['weights']['price']}, Quality {addn['overrides']['weights']['quality']}"], "source": "addenda"}
    weights_ok = bool(w["found"] and abs(round(w["total"], 2) - 100.0) < 0.01)
    checks.append(Check(token="tender:criteria:weights_disclosed", ok=weights_ok, details=f"found={int(w['found'])}; total={round(w['total'],2)}; count={w['count']}"))
    rows.append({"type":"criteria_weights","asset_id":_asset_id_from(args.tender_zip, "pack"),"found":w["found"],"total":round(w["total"],2),"count":w["count"],"files":w["files"],"sample_lines":w["sample_lines"],"source":w.get("source","tender"),"ts":record_ts()})

    f = extract_formula(args.tender_zip)
    checks.append(Check(token="tender:criteria:formula_disclosed", ok=bool(f["found"]), details=f"found={int(f['found'])}; files={len(f['files'])}"))
    rows.append({"type":"criteria_formula","asset_id":_asset_id_from(args.tender_zip, "pack"),"found":f["found"],"files":f["files"],"sample_lines":f["sample_lines"],"ts":record_ts()})

    coh = parse_notice_itt(args.tender_zip)
    checks.append(Check(token="tender:coherence:notice_itt_consistent", ok=bool(coh.get("ok", False)), details=f"notice_proc={coh['notice']['procedure'] or ''}; itt_proc={coh['itt']['procedure'] or ''}; notice_lots={coh['notice']['lots'] or ''}; itt_lots={coh['itt']['lots'] or ''}"))
    rows.append({"type":"coherence","asset_id":_asset_id_from(args.tender_zip, "pack"),"fields_checked":["procedure","lots"],"notice":coh["notice"],"itt":coh["itt"],"ok":coh["ok"],"ts":record_ts()})

    reqs = extract_requirements(args.tender_zip)
    mapped = map_offer(args.offer_zip, reqs)
    mand_total = sum(1 for r in mapped if r["priority"] == "mandatory")
    mand_present = sum(1 for r in mapped if r["priority"] == "mandatory" and r["state"] == "present")
    mand_review = sum(1 for r in mapped if r["priority"] == "mandatory" and r["state"] == "review")
    mand_missing = mand_total - mand_present - mand_review
    rows.extend({
        "type":"requirement",
        "asset_id":_asset_id_from(args.tender_zip, "pack"),
        "req_id": r["req_id"],
        "priority": r["priority"],
        "doc": r["doc"],
        "doc_sha256": r["doc_sha256"],
        "char_start": r["char_start"],
        "char_end": r["char_end"],
        "text_snippet": r["text_snippet"],
        "state": r["state"],
        "state_reason": r["state_reason"],
        "ts": record_ts()
    } for r in mapped)
    checks.append(Check(token="tender:req:mandatories_all_present", ok=(mand_total > 0 and mand_missing == 0 and mand_review == 0), details=f"present={mand_present}; review={mand_review}; missing={mand_missing}; total={mand_total}"))

    pc = detect_prohibited_conditions(args.offer_zip) if args.offer_zip else {"found": False, "files": [], "sample_lines": [], "count": 0}
    checks.append(Check(token="tender:offer:prohibited_conditions_absent", ok=(not pc["found"]), details=f"violations={pc['count']}"))
    rows.append({"type":"offer_prohibited","asset_id":_asset_id_from(args.offer_zip or '', "offer" if args.offer_zip else "offer"),"found":pc["found"],"files":pc["files"],"sample_lines":pc["sample_lines"],"ts":record_ts()})

    fmt = check_format_ok(args.tender_zip, args.offer_zip, limit_override=addenda_limit) if args.offer_zip else {"found_limit": False, "limit": None, "offer_words": 0, "ok": False, "reason":"NO_OFFER"}
    checks.append(Check(token="tender:offer:format_ok", ok=fmt["ok"], details=f"limit={fmt['limit'] if fmt['found_limit'] else 'NA'}; words={fmt['offer_words']}; reason={fmt['reason']}"))
    rows.append({"type":"offer_format","asset_id":_asset_id_from(args.offer_zip or '', "offer" if args.offer_zip else "offer"),"found_limit":fmt["found_limit"],"limit":fmt["limit"],"offer_words":fmt["offer_words"],"ok":fmt["ok"],"reason":fmt["reason"],"ts":record_ts()})

    addenda_applied = bool(addn["found"] and (addenda_limit is not None or w.get("source") == "addenda"))
    rows.append({"type":"addenda","asset_id":_asset_id_from(args.tender_zip, "pack"),"found":addn["found"],"files":addn["files"],"items":addn["items"],"overrides_used":addenda_applied,"ts":record_ts()})
    checks.append(Check(token="tender:qna:addenda_applied", ok=addenda_applied, details=f"files={len(addn['files'])}; items={len(addn['items'])}"))

    price = validate_prices(args.offer_zip) if args.offer_zip else {"found": False, "ok": False, "rows_checked": 0, "row_errors": 0, "declared_sum": 0.0, "computed_sum": 0.0, "files": []}
    checks.append(Check(token="tender:price:arithmetic_ok", ok=price["ok"], details=f"rows={price['rows_checked']}; errors={price['row_errors']}; sum_declared={price['declared_sum']}; sum_computed={price['computed_sum']}"))
    rows.append({"type":"price_check","asset_id":_asset_id_from(args.offer_zip or '', "offer" if args.offer_zip else "offer"),"found":price["found"],"ok":price["ok"],"rows_checked":price["rows_checked"],"row_errors":price["row_errors"],"declared_sum":price["declared_sum"],"computed_sum":price["computed_sum"],"files":price["files"],"ts":record_ts()})

    total_size = sum(m["size"] for m in tender_members) + sum(m["size"] for m in offer_members)
    rows.append({"type":"summary","asset_id":_asset_id_from(args.tender_zip, "pack"),"docs_total": len(tender_members) + len(offer_members),"bytes_total": total_size, "ts": record_ts()})

    write_receipts_and_root(receipts_path, root_path, rows)
    write_matrices(args.out, mapped)

    failing_enforced = None
    if args.posture == "enforce":
        for c in checks:
            if c.token in ENFORCED_TOKENS and not c.ok:
                failing_enforced = c.token
                break

    asset_id = _asset_id_from(args.offer_zip or args.tender_zip, "offer" if args.offer_zip else "pack")
    if failing_enforced:
        record = build_decision(TOOL, asset_id, token=failing_enforced, decision="block", posture="enforce", checks=checks, pack=PACK, registry_sha=args.registry_sha)
    else:
        record = build_decision(TOOL, asset_id, token="ok", decision="allow", posture=args.posture, checks=checks, pack=PACK, registry_sha=args.registry_sha)

    print(json.dumps(record, ensure_ascii=False))
    print(record["reason"], file=sys.stderr)
    return record["exit_code"]

if __name__ == "__main__":
    raise SystemExit(main())
