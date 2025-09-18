import argparse, json, os, zipfile
from datetime import datetime, timezone
from .version import VERSION
from .bedrock import build_decision, Check
from .merkle import write_receipts_and_root
from .service_levels import extract as extract_service_levels
from .contract_terms import extract as extract_contract_terms
from .krav_csv import extract_from_zip as extract_krav_csv
from .matrix import write_service_levels_csv, write_contract_terms_csv, write_requirements_matrix_csv, write_evaluation_items_csv

TOOL = "tender-digest"
PACK = "tender-core"

def _iso_now():
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def _asset_id_from(path, kind):
    base = os.path.basename(path)
    name = os.path.splitext(base)[0]
    return f"tender:{kind}/{name}"

def _read_text_from_zip(zf, name):
    try:
        return zf.read(name).decode("utf-8", "ignore")
    except KeyError:
        return None

def _stamp_rows(rows, ts):
    for r in rows:
        if "ts" not in r:
            r["ts"] = ts
    return rows

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--tender-zip", required=True)
    p.add_argument("--offer-zip")
    p.add_argument("--out", required=True)
    p.add_argument("--posture", default="advice")
    p.add_argument("--registry-sha")
    args = p.parse_args()

    os.makedirs(args.out, exist_ok=True)
    proof_dir = os.path.join(args.out, "proof")
    matrix_dir = os.path.join(args.out, "matrix")
    os.makedirs(proof_dir, exist_ok=True)
    os.makedirs(matrix_dir, exist_ok=True)

    now_ts = _iso_now()
    tender_members = []
    with zipfile.ZipFile(args.tender_zip, "r") as z:
        for zi in z.infolist():
            if not zi.is_dir():
                tender_members.append({"name": zi.filename, "size": zi.file_size})
        bilag10_txt = _read_text_from_zip(z, "Bilag10.txt")
        ramme_txt = _read_text_from_zip(z, "Rammeavtale.txt")
        req_rows, eval_rows, krav_receipts = extract_krav_csv(z, _asset_id_from(args.tender_zip,"pack"))

    rows = []
    checks = []
    rows.append({"type":"summary","asset_id":_asset_id_from(args.tender_zip,"pack"),
                 "docs_total":len(tender_members),"bytes_total":sum(m["size"] for m in tender_members),"ts":now_ts})
    checks.append(Check(token="tender:pack:parse_ok", ok=True,
                        details=f"docs={len(tender_members)}; allowed={len(tender_members)}", source=None))

    if req_rows or eval_rows:
        write_requirements_matrix_csv(matrix_dir, req_rows)
        write_evaluation_items_csv(matrix_dir, eval_rows)
        rows.extend(_stamp_rows(krav_receipts, now_ts))
        checks.append(Check(token="tender:krav:matrices_built", ok=True,
                            details=f"req={len(req_rows)}; eval={len(eval_rows)}", source=None))

    if bilag10_txt:
        features, svc_receipts = extract_service_levels(bilag10_txt, _asset_id_from(args.tender_zip,"pack"))
        rows.extend(_stamp_rows(svc_receipts, now_ts))
        write_service_levels_csv(matrix_dir, features)
        checks.append(Check(token="tender:service:levels_matrix_built", ok=len(features)>0,
                            details=f"features={len(features)}", source=None))

    if ramme_txt:
        terms, ct_receipts = extract_contract_terms(ramme_txt, _asset_id_from(args.tender_zip,"pack"))
        rows.extend(_stamp_rows(ct_receipts, now_ts))
        write_contract_terms_csv(matrix_dir, terms)
        checks.append(Check(token="tender:contract:terms_extracted", ok=len(terms)>0,
                            details=f"keys={len(terms)}", source=None))

    receipts_path = os.path.join(proof_dir, "receipts.jsonl")
    root_path = os.path.join(proof_dir, "root.txt")
    write_receipts_and_root(receipts_path, root_path, rows)

    asset_id = _asset_id_from(args.tender_zip, "pack")
    record = build_decision(TOOL, asset_id, token="ok", decision="allow", posture=args.posture,
                            checks=checks, pack=PACK, registry_sha=args.registry_sha)
    print(json.dumps(record, ensure_ascii=False))
    print(record["reason"])
    return record["exit_code"]

if __name__ == "__main__":
    raise SystemExit(main())
