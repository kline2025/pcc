import argparse, os, zipfile
from .version import VERSION
from .bedrock import build_decision, Check
from .merkle import write_receipts_and_root
from .matrix import write_forms_constraints_csv, write_submission_checklist_csv, write_criteria_and_formula_csv, write_price_schema_csv, write_contract_terms_csv, write_requirements_matrix_csv
from .extract_hso_byggc import extract_itt_text, extract_konkurranseskjema_text, extract_avtale_text, extract_endringsbest_text, extract_c21_text

def _read_txt(zf, names):
    for n in names:
        try:
            return zf.read(n).decode("utf-8","ignore"), n
        except KeyError:
            continue
    return None, None

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--tender-zip",required=True)
    ap.add_argument("--out",required=True)
    ap.add_argument("--posture",default="advice")
    args=ap.parse_args()

    os.makedirs(args.out,exist_ok=True)
    proof_dir=os.path.join(args.out,"proof"); os.makedirs(proof_dir,exist_ok=True)
    matrix_dir=os.path.join(args.out,"matrix"); os.makedirs(matrix_dir,exist_ok=True)

    rows=[]; checks=[]

    with zipfile.ZipFile(args.tender_zip,"r") as z:
        itt_txt,_ = _read_txt(z, ["000_Konkurransebestemmelser.txt","Konkurransebestemmelser.txt"])
        pris_txt,_ = _read_txt(z, ["002_Konkurranseskjema_13368.txt","Konkurranseskjema.txt"])
        avtale_txt,_ = _read_txt(z, ["A0 DSV Avtaledokument.txt","Avtaledokument.txt"])
        endr_txt,_ = _read_txt(z, ["B2_Endringsbestemmelser.txt","Endringsbestemmelser.txt"])
        c21_txt,_ = _read_txt(z, ["C21_Felles.txt","C21.txt"])

        if itt_txt:
            fc, subm, cf, rc = extract_itt_text(itt_txt, "000_Konkurransebestemmelser.pdf")
            if fc: write_forms_constraints_csv(matrix_dir, fc)
            if subm: write_submission_checklist_csv(matrix_dir, subm)
            if cf: write_criteria_and_formula_csv(matrix_dir, cf)
            rows.extend(rc)
            if any(r for r in cf if r.get("criterion")=="Pris"): checks.append(Check(token="tender:criteria:formula_disclosed", ok=True, details="price model present", source=None))

        if pris_txt:
            ps_rows, rc2 = extract_konkurranseskjema_text(pris_txt, "002_Konkurranseskjema_13368.pdf")
            for r in ps_rows:
                write_price_schema_csv(matrix_dir, r["sheet"], r["headers"].split("|"), eval(r["constants"]))
            rows.extend(rc2)

        term_dict={}; rc3=[]
        if avtale_txt:
            t,rca,req = extract_avtale_text(avtale_txt, "A0 DSV Avtaledokument.pdf")
            term_dict.update(t); rc3.extend(rca)
            if req: write_requirements_matrix_csv(matrix_dir, req)
        if endr_txt:
            t2, rcb = extract_endringsbest_text(endr_txt, "B2_Endringsbestemmelser.pdf")
            term_dict.update(t2); rc3.extend(rcb)
        if term_dict:
            write_contract_terms_csv(matrix_dir, term_dict)
            checks.append(Check(token="tender:contract:terms_extracted", ok=True, details=f"keys={len(term_dict)}", source=None))
        rows.extend(rc3)

        if c21_txt:
            req_rows, rcc21 = extract_c21_text(c21_txt, "C21_Felles.pdf")
            if req_rows: write_requirements_matrix_csv(matrix_dir, req_rows)
            rows.extend(rcc21)

    receipts_path=os.path.join(proof_dir,"receipts.jsonl")
    root_path=os.path.join(proof_dir,"root.txt")
    write_receipts_and_root(receipts_path, root_path, rows)

    asset_id=f"tender:pack/{os.path.splitext(os.path.basename(args.tender_zip))[0]}"
    record=build_decision("hso-byggc-digest", asset_id, token="ok", decision="allow", posture=args.posture, checks=checks, pack="tender-core", registry_sha=None)
    print(record)
    print(record["reason"])
    return 0

if __name__=="__main__":
    raise SystemExit(main())
