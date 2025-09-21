import argparse, os, zipfile
from .version import VERSION
from .bedrock import build_decision, Check
from .merkle import write_receipts_and_root
from .matrix import write_forms_constraints_csv, write_submission_checklist_csv, write_criteria_and_formula_csv, write_price_schema_csv, write_requirements_matrix_csv, write_contract_terms_csv
from .extract_hmn_invasive import extract_itt, extract_spec, extract_price, extract_contract

def _read(zf, names):
    for n in names:
        try:
            return zf.read(n).decode("utf-8","ignore"), n
        except KeyError:
            continue
    return None, None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--tender-zip", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--posture", default="advice")
    args=ap.parse_args()

    os.makedirs(args.out, exist_ok=True)
    proof_dir=os.path.join(args.out,"proof"); os.makedirs(proof_dir, exist_ok=True)
    matrix_dir=os.path.join(args.out,"matrix"); os.makedirs(matrix_dir, exist_ok=True)

    rows=[]; checks=[]

    with zipfile.ZipFile(args.tender_zip,"r") as z:
        itt_txt,_ = _read(z, ["Konkurransebestemmelser.txt","Konkurransebestemmelser åpen anbudskonkurranse Invasive trykksett.txt","ITT.txt"])
        krav_txt,_ = _read(z, ["Vedlegg 02 Kravspesifikasjon.txt","Kravspesifikasjon.txt"])
        pris_txt,_ = _read(z, ["Vedlegg 03 Prisskjema.txt","Prisskjema.txt"])
        ramme_txt,_ = _read(z, ["Vedlegg 07 Rammeavtale.txt","Rammeavtale.txt"])

        if itt_txt:
            fc, subm, cf, rc = extract_itt(itt_txt, "Konkurransebestemmelser.pdf")
            if fc: write_forms_constraints_csv(matrix_dir, fc)
            if subm: write_submission_checklist_csv(matrix_dir, subm)
            if cf: write_criteria_and_formula_csv(matrix_dir, cf)
            rows.extend(rc)
            if any(r for r in cf if r.get("criterion","").lower()=="pris"): checks.append(Check(token="tender:criteria:formula_disclosed", ok=True, details="proportional 10*(lowest/evaluated)", source=None))

        if krav_txt:
            req_rows, rc2 = extract_spec(krav_txt, "Vedlegg 02 Kravspesifikasjon.pdf")
            if req_rows: write_requirements_matrix_csv(matrix_dir, req_rows)
            rows.extend(rc2)

        if pris_txt:
            const, rc3 = extract_price(pris_txt, "Vedlegg 03 Prisskjema.pdf")
            if const: write_price_schema_csv(matrix_dir, "Prisskjema", [], const)
            rows.extend(rc3)

        if ramme_txt:
            terms, rc4 = extract_contract(ramme_txt, "Vedlegg 07 Rammeavtale.docx")
            if terms:
                write_contract_terms_csv(matrix_dir, terms)
                checks.append(Check(token="tender:contract:terms_extracted", ok=True, details=f"keys={len(terms)}", source=None))
            rows.extend(rc4)

    receipts=os.path.join(proof_dir,"receipts.jsonl")
    root=os.path.join(proof_dir,"root.txt")
    write_receipts_and_root(receipts, root, rows)

    asset_id=f"tender:pack/{os.path.splitext(os.path.basename(args.tender_zip))[0]}"
    record=build_decision("hmn-invasive-digest", asset_id, token="ok", decision="allow", posture=args.posture, checks=checks, pack="tender-core", registry_sha=None)
    print(record)
    print(record["reason"])
    return 0

if __name__=="__main__":
    raise SystemExit(main())
