import argparse, os, zipfile
from .bedrock import build_decision, Check
from .merkle import write_receipts_and_root
from .matrix import (
    write_forms_constraints_csv, write_submission_checklist_csv,
    write_criteria_and_formula_csv, write_contract_terms_csv, write_price_schema_csv, write_requirements_matrix_csv
)
from .extract_multilot_office import extract_office_itt, extract_office_price_schema, extract_office_spec, extract_office_contract, extract_office_logistics, extract_office_edi

def _read(zf, names):
    for n in names:
        try:
            return zf.read(n).decode("utf-8","ignore"), n
        except KeyError:
            continue
    return None, None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tender-zip", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--posture", default="advice")
    args = ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    proof_dir  = os.path.join(args.out, "proof");  os.makedirs(proof_dir, exist_ok=True)
    matrix_dir = os.path.join(args.out, "matrix"); os.makedirs(matrix_dir, exist_ok=True)

    rows, checks = [], []

    with zipfile.ZipFile(args.tender_zip, "r") as z:
        itt_txt, _ = _read(z, [
            "Konkurransebestemmelser - kontorrekvisita og batterier.txt",
            "Konkurransebestemmelser_kontorrekvisita_batterier.txt",
            "Konkurransebestemmelser.txt"
        ])

        price_txt, _ = _read(z, [
            "Bilag 1 - Prisskjema.txt",
            "Bilag 1 Prisskjema.txt",
            "Prisskjema.txt"
        ])

        spec_txt, _ = _read(z, [
            "Bilag 2 - Kravspesifikasjon.txt",
            "Kravspesifikasjon.txt"
        ])
        contract_txt, _ = _read(z, [
            "Bilag 13 - Rammeavtale.txt",
            "Rammeavtale.txt"
        ])

        if itt_txt:
            fc, chk, cf, terms, rc = extract_office_itt(itt_txt, "Konkurransebestemmelser.pdf")
            if fc:    write_forms_constraints_csv(matrix_dir, fc)
            if chk:   write_submission_checklist_csv(matrix_dir, chk)
            if cf:    write_criteria_and_formula_csv(matrix_dir, cf)
            if terms: write_contract_terms_csv(matrix_dir, terms)
            rows.extend(rc)
        if price_txt:
            ps_rows, rc2 = extract_office_price_schema(price_txt, "Bilag_1_Prisskjema.pdf")
            for r in ps_rows:
                write_price_schema_csv(matrix_dir, r["sheet"], r["headers"], r["constants"])
            rows.extend(rc2)
        if spec_txt:
            req_rows, rc3 = extract_office_spec(spec_txt, "Bilag_2_Kravspesifikasjon.pdf")
            if req_rows:
                write_requirements_matrix_csv(matrix_dir, req_rows)
            rows.extend(rc3)
        if contract_txt:
            c_terms, c_req, rc4 = extract_office_contract(contract_txt, "Bilag_13_Rammeavtale.pdf")
            if c_terms:
                write_contract_terms_csv(matrix_dir, c_terms)
            if c_req:
                write_requirements_matrix_csv(matrix_dir, c_req)
            rows.extend(rc4)
        if logi_txt:
            lg_terms, lg_req, lg_rc = extract_office_logistics(logi_txt, "Bilag_7_Logistikkbetingelser.pdf")
            if lg_terms:
                write_contract_terms_csv(matrix_dir, lg_terms)
            if lg_req:
                write_requirements_matrix_csv(matrix_dir, lg_req)
            rows.extend(lg_rc)
        if edi_txt:
            edi_terms, edi_req, edi_rc = extract_office_edi(edi_txt, "Bilag_9_Elektronisk_samhandlingsavtale_HN.pdf")
            if edi_terms:
                write_contract_terms_csv(matrix_dir, edi_terms)
            if edi_req:
                write_requirements_matrix_csv(matrix_dir, edi_req)
            rows.extend(edi_rc)

            if cf:    checks.append(Check(token="tender:criteria:weights_disclosed", ok=True, details=f"{len(cf)} rows", source=None))
            if "lots:count" in terms or any(r.get("item")=="lots_count" for r in fc):
                checks.append(Check(token="tender:lots:declared", ok=True, details=str(terms.get("lots:count","")), source=None))
            if "price:eval_method" in terms:
                checks.append(Check(token="tender:criteria:formula_disclosed", ok=True, details=terms["price:eval_method"], source=None))

    receipts_path = os.path.join(proof_dir, "receipts.jsonl")
    root_path     = os.path.join(proof_dir, "root.txt")
    write_receipts_and_root(receipts_path, root_path, rows)

    asset_id = f"tender:pack/{os.path.splitext(os.path.basename(args.tender_zip))[0]}"
    record = build_decision("multilot-office-digest", asset_id, token="ok", decision="allow",
                            posture=args.posture, checks=checks, pack="tender-core", registry_sha=None)
    print(record)
    print(record["reason"])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
