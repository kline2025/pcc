import argparse, os, zipfile
from .bedrock import build_decision, Check
from .merkle import write_receipts_and_root
from .matrix import (
    write_forms_constraints_csv, write_contract_terms_csv, write_requirements_matrix_csv
)
from .extract_dps import extract_dps_rules
from .extract_ssa_b import extract_ssa_b_contract, extract_ssa_b_bilag
from .extract_dpa_2020 import extract_dpa2020_contract, extract_dpa2020_bilag

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
        kval_txt,_ = _read(z, [
            "Kvalifikasjonsgrunnlag DPS.txt",
            "Kvalifikasjonsgrunnlag: Etablering og bruk av dynamisk innkjøpsordning.txt",
            "Document-4.txt", "DPS_kvalifikasjon.txt"
        ])

        if kval_txt:
            fc, terms, req, rc = extract_dps_rules(kval_txt, "Kvalifikasjonsgrunnlag_DPS.pdf")
            if fc:    write_forms_constraints_csv(matrix_dir, fc)
            if terms: write_contract_terms_csv(matrix_dir, terms)
            if req:   write_requirements_matrix_csv(matrix_dir, req)
            rows.extend(rc)

            if terms.get("dps:enabled"): checks.append(Check(token="tender:dps:enabled", ok=True, details="true", source=None))
            if terms.get("dps:rolling_admission"): checks.append(Check(token="tender:dps:rolling_admission", ok=True, details="true", source=None))
        if ssab_txt:
            c_terms, c_req, c_rc = extract_ssa_b_contract(ssab_txt, "SSA-B_generell_2015.docx")
            if c_terms: write_contract_terms_csv(matrix_dir, c_terms)
            if c_req:   write_requirements_matrix_csv(matrix_dir, c_req)
            rows.extend(c_rc)
        if ssab_bilag_txt:
            b_req, b_rc = extract_ssa_b_bilag(ssab_bilag_txt, "SSA-B_bilag_2015.docx")
            if b_req: write_requirements_matrix_csv(matrix_dir, b_req)
            rows.extend(b_rc)
        if dpa_main_txt:
            dpa_terms, dpa_req1, dpa_rc1 = extract_dpa2020_contract(dpa_main_txt, "DPA_generell_2020.docx")
            if dpa_terms: write_contract_terms_csv(matrix_dir, dpa_terms)
            if dpa_req1: write_requirements_matrix_csv(matrix_dir, dpa_req1)
            rows.extend(dpa_rc1)
        if dpa_bilag_txt:
            dpa_req2, dpa_rc2 = extract_dpa2020_bilag(dpa_bilag_txt, "DPA_bilag_2020.docx")
            if dpa_req2: write_requirements_matrix_csv(matrix_dir, dpa_req2)
            rows.extend(dpa_rc2)

    receipts = os.path.join(proof_dir, "receipts.jsonl")
    root     = os.path.join(proof_dir, "root.txt")
    write_receipts_and_root(receipts, root, rows)

    asset_id = f"tender:pack/{os.path.splitext(os.path.basename(args.tender_zip))[0]}"
    record = build_decision("dps-digest", asset_id, token="ok", decision="allow",
                            posture=args.posture, checks=checks, pack="tender-core", registry_sha=None)
    print(record); print(record["reason"])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
