import argparse, os, zipfile
from .bedrock import build_decision, Check
from .merkle import write_receipts_and_root
from .matrix import (
    write_forms_constraints_csv, write_criteria_and_formula_csv,
    write_requirements_matrix_csv, write_contract_terms_csv
)
from .extract_ns8406_simple import extract_ns8406_itt, extract_ns8406_contract, extract_ns3420_boq, extract_ns8406_env_sha, extract_ns8406_mop, extract_ns8406_overvaking

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

    with zipfile.ZipFile(args.tender_zip,"r") as z:
        itt_txt,_  = _read(z, ["Konkurransegrunnlag - Rossevann VV (E01).txt",
                               "Konkurransegrunnlag - Rossevann VV.txt",
                               "Konkurransegrunnlag.txt"])
        c03_txt,_  = _read(z, ["Vedlegg 03 - Standard kontraktsbestemmelser NS 8406.txt",
                               "Standard kontraktsbestemmelser NS 8406.txt",
                               "NS8406_kontraktsbestemmelser.txt"])

        besk_txt,_ = _read(z, [
            "10260224-TVF-BESK-001_E01_REV01.txt",
            "NS3420_beskrivelse.txt",
            "Beskrivelse.txt"
        ])

        if itt_txt:
            fc, cf, req, rc = extract_ns8406_itt(itt_txt, "Konkurransegrunnlag_RossevannVV_E01.pdf")
            if fc:   write_forms_constraints_csv(matrix_dir, fc)
            if cf:   write_criteria_and_formula_csv(matrix_dir, cf)
            if req:  write_requirements_matrix_csv(matrix_dir, req)
            rows.extend(rc)

            if cf: checks.append(Check(token="tender:criteria:weights_disclosed", ok=True, details=f"{len(cf)} rows", source=None))

        if c03_txt:
            terms, creq, rc2 = extract_ns8406_contract(c03_txt, "Vedlegg03_NS8406_standardbestemmelser.pdf")
            if terms: write_contract_terms_csv(matrix_dir, terms)
            if creq:  write_requirements_matrix_csv(matrix_dir, creq)
            rows.extend(rc2)
            checks.append(Check(token="tender:contract:family", ok=True, details="NS8406", source=None))
        if besk_txt:
            ps_rows, rc3 = extract_ns3420_boq(besk_txt, "TVF-BESK-001_E01_REV01.pdf")
            for r in ps_rows:
                write_price_schema_csv(matrix_dir, r["sheet"], r["headers"], r["constants"])
            req_rows, rc4 = extract_ns8406_env_sha(besk_txt, "TVF-BESK-001_E01_REV01.pdf")
            if req_rows:
                write_requirements_matrix_csv(matrix_dir, req_rows)
            rows.extend(rc3 + rc4)
        if mop_txt:
            m_terms, m_reqs, m_rc = extract_ns8406_mop(mop_txt, "MOP.pdf")
            if m_terms:
                write_contract_terms_csv(matrix_dir, m_terms)
            if m_reqs:
                write_requirements_matrix_csv(matrix_dir, m_reqs)
            rows.extend(m_rc)
        if ov_txt:
            o_terms, o_reqs, o_rc = extract_ns8406_overvaking(ov_txt, "Overvåkningsplan.pdf")
            if o_terms:
                write_contract_terms_csv(matrix_dir, o_terms)
            if o_reqs:
                write_requirements_matrix_csv(matrix_dir, o_reqs)
            rows.extend(o_rc)

    receipts = os.path.join(proof_dir, "receipts.jsonl")
    root     = os.path.join(proof_dir, "root.txt")
    write_receipts_and_root(receipts, root, rows)

    asset_id = f"tender:pack/{os.path.splitext(os.path.basename(args.tender_zip))[0]}"
    record = build_decision("ns8406-simple-digest", asset_id, token="ok", decision="allow",
                            posture=args.posture, checks=checks, pack="tender-core", registry_sha=None)
    print(record)
    print(record["reason"])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
