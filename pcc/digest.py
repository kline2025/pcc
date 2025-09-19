import argparse, json, os, zipfile
from datetime import datetime, timezone
from .version import VERSION
from .bedrock import build_decision, Check
from .merkle import write_receipts_and_root
from .service_levels import extract as extract_service_levels
from .contract_terms import extract as extract_contract_terms
from .krav_csv import extract_from_zip as extract_krav_csv
from .itt import extract as extract_itt
from .price_schema import extract as extract_price_schema
from .matrix import write_criteria_and_formula_csv, write_submission_checklist_csv, write_variants_csv
from .underlag_nv_text import extract_constants as extract_nv_text
from .submission_checklist import extract_from_itt as extract_subm_itt
from .criteria_and_formula import extract_from_itt as extract_cf_itt
from .contract_eie_meglerstandard import extract as extract_eie
from .contract_leie_statsbygg import extract as extract_leie
from .variants import detect_from_path
from .formula_detect import scan_zip_for_formula
from .addenda_diff import scan as scan_addenda
from .matrix import (
    write_service_levels_csv,
    write_contract_terms_csv,
    write_requirements_matrix_csv,
    write_evaluation_items_csv,
    write_price_schema_csv,
    write_forms_constraints_csv, write_criteria_and_formula_csv, write_submission_checklist_csv, write_variants_csv, write_criteria_and_formula_csv, write_submission_checklist_csv, write_variants_csv, write_criteria_and_formula_csv, write_submission_checklist_csv, write_variants_csv, write_variants_csv, write_addenda_diff_csv,
)

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
        cf_rows=[]
        cf_total=None
        cf_model=False
        cf_scoring=None
        nv_consts={}
        nv_written=False
        nv_receipts=[]
        itt_text=None
        for zi in z.infolist():
            if zi.is_dir():
                continue
            n=zi.filename.lower()
            if n.endswith('itt.txt'):
                itt_text=z.read(zi.filename).decode('utf-8','ignore')
            if n.endswith('.txt') and ('underlag' in n or 'nåverdi' in n or 'npv' in n or 'prisskjema' in n):
                t=z.read(zi.filename).decode('utf-8','ignore')
                c, rc = extract_nv_text(t)
                if c:
                    nv_consts.update(c)
                    nv_receipts.extend(rc)
        if itt_text:
            cf_rows, cf_total, cf_model, cf_scoring, cf_receipts = extract_cf_itt(itt_text)

        for zi in z.infolist():
            if not zi.is_dir():
                tender_members.append({"name": zi.filename, "size": zi.file_size})
        bilag10_txt = _read_text_from_zip(z, "Bilag10.txt")
        ramme_txt = _read_text_from_zip(z, "Rammeavtale.txt")
        itt_txt    = _read_text_from_zip(z, "ITT.txt")
        req_rows, eval_rows, krav_receipts = extract_krav_csv(z, _asset_id_from(args.tender_zip,"pack"))
        price_entries, price_receipts = extract_price_schema(z, _asset_id_from(args.tender_zip,"pack"))

    rows = []
    formula_ok=False
    formula_receipts=[]
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

    if itt_txt:
        itt_rows, itt_checks = extract_itt(itt_txt, _asset_id_from(args.tender_zip,"pack"))
        fc_rows = [ r for r in itt_rows if r.get("type") in ("submission","forms") ]
        if fc_rows:
            write_forms_constraints_csv(matrix_dir, fc_rows)
        rows.extend(_stamp_rows(itt_rows, now_ts))
        if itt_text:
            cf_rows, cf_total, cf_model, cf_scoring, cf_receipts = extract_cf_itt(itt_text)
            subm_rows = extract_subm_itt(itt_text)
            if subm_rows:
                write_submission_checklist_csv(matrix_dir, subm_rows)
                rows.append({'type':'submission_manifest','asset_id':_asset_id_from(args.tender_zip,'pack'),'count':len(subm_rows),'ts':now_ts})
        if cf_rows:
            for r in cf_rows:
                rcrit=(r.get('criterion','') or '').lower(); r['group']='price' if ('pris' in rcrit or 'totalkostnad' in rcrit or 'total kostnad' in rcrit) else 'quality'
                r['price_model']='npv_in_prisskjema' if cf_model else ''
                r['scoring_model']=cf_scoring or ''
                r['model_anchor']='Prisskjema'
            write_criteria_and_formula_csv(matrix_dir, cf_rows)
            rows.extend(_stamp_rows(cf_receipts, now_ts))
        if nv_consts:
            from .matrix import write_price_schema_csv
            if not nv_written:
            write_price_schema_csv(matrix_dir, 'UnderlagNV_text', [], nv_consts)
            rows.extend(_stamp_rows(nv_receipts, now_ts))
            nv_written=True
        if cf_rows:
            for r in cf_rows:
                rcrit=(r.get('criterion','') or '').lower(); r['group']='price' if ('pris' in rcrit or 'totalkostnad' in rcrit or 'total kostnad' in rcrit) else 'quality'
                r['price_model']='npv_in_prisskjema' if cf_model else ''
                r['scoring_model']=cf_scoring or ''
                r['model_anchor']='Prisskjema'
            write_criteria_and_formula_csv(matrix_dir, cf_rows)
            rows.extend(_stamp_rows(cf_receipts, now_ts))
        if nv_consts:
            from .matrix import write_price_schema_csv
            if not nv_written:
            write_price_schema_csv(matrix_dir, 'UnderlagNV_text', [], nv_consts)
            rows.extend(_stamp_rows(nv_receipts, now_ts))
            nv_written=True
        vrows = detect_from_path(args.tender_zip)
        if vrows:
            any_decl = any(v.get('in_itt') or v.get('in_price') or v.get('in_contracts') for v in vrows)
            if any_decl:
                summary = "; ".join([f"{v['variant']}=ITT:{int(bool(v['in_itt']))}/Price:{int(bool(v['in_price']))}/Contracts:{int(bool(v['in_contracts']))}" for v in vrows])
                checks.append(Check(token="tender:variants:declared", ok=True, details=summary, source=None))
        if vrows:
            write_variants_csv(matrix_dir, vrows)
        if cf_model:
            checks.append(Check(token="tender:criteria:formula_disclosed", ok=True, details="present_in_text", source=None))

        for tok, ok, det in itt_checks:
            checks.append(Check(token=tok, ok=ok, details=det, source=None))

    if price_entries:
        for sheet, header, constants in price_entries:
            write_price_schema_csv(matrix_dir, sheet, header, constants)
        rows.extend(_stamp_rows(price_receipts, now_ts))

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
