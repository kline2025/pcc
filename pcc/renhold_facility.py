import argparse, os, zipfile
from .bedrock import build_decision, Check
from .merkle import write_receipts_and_root
from .matrix import write_forms_constraints_csv, write_submission_checklist_csv, write_criteria_and_formula_csv, write_requirements_matrix_csv, write_service_sla_csv, write_price_schema_csv, write_contract_terms_csv
from .extract_renhold_facility import extract_renhold_itt, extract_renhold_spec, extract_renhold_price_forms, extract_renhold_contract, extract_renhold_akrim, extract_renhold_akrim_selfreport, extract_renhold_experience

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
        itt_txt,_  = _read(z, ["Konkurransebestemmelser Diverse Renholdstjenster.txt","Konkurransebestemmelser Diverse Renholdstjenester.txt","Konkurransebestemmelser.txt"])
        krav_txt,_ = _read(z, ["Bilag 1 Kravspesifikasjon.txt","Kravspesifikasjon.txt"])
        price_pdf_txt,_  = _read(z, ["Vedlegg 6 Prisskjema Excell.txt","Prisskjema Excel.txt","Vedlegg_6_Prisskjema.txt"]) 
        price_docx_txt,_ = _read(z, ["Bilag 2 Prisskjema.txt","Prisskjema.txt"]) 
        ramme_txt,_      = _read(z, ["Rammeavtale Div. Renholdstjenester.txt","Rammeavtale.txt"]) 
        akrim_txt,_      = _read(z, ["Bilag 3 Krav akrim Renhold.txt","Krav akrim Renhold.txt","Bilag_3_AKRIM.txt"]) 
        selfrep_txt,_   = _read(z, ["Bilag 4 Egenrapportering akrim Renhold.txt","Egenrapportering akrim Renhold.txt","Bilag_4_Egenrapportering.txt"]) 
        exp_txt,_       = _read(z, ["Vedlegg 2 - Svarskjema erfaring.txt","Svarskjema erfaring.txt","Vedlegg_2_Svarskjema_erfaring.txt"]) 

        if itt_txt:
            fc, chk, cf, rc = extract_renhold_itt(itt_txt, "Konkurransebestemmelser_Renholdstjenester.docx")
            if fc:  write_forms_constraints_csv(matrix_dir, fc)
            if chk: write_submission_checklist_csv(matrix_dir, chk)
            if cf:  write_criteria_and_formula_csv(matrix_dir, cf)
            rows.extend(rc)
            if any(c.get("group")=="price" for c in cf):
                checks.append(Check(token="tender:criteria:formula_disclosed", ok=True, details="linear price scoring present", source=None))

        if krav_txt:
            req, sla, rc2 = extract_renhold_spec(krav_txt, "Bilag_1_Kravspesifikasjon.pdf")
            if req: write_requirements_matrix_csv(matrix_dir, req)
            if sla: write_service_sla_csv(matrix_dir, sla)
            rows.extend(rc2)
            if sla: checks.append(Check(token="tender:service:sla_extracted", ok=True, details=f"keys={len(sla)}", source=None))
        # price schema + invoice terms
        if price_pdf_txt or price_docx_txt:
            ps_rows, p_terms, rcP = extract_renhold_price_forms(price_pdf_txt or "", "Vedlegg_6_Prisskjema_Excel.pdf", price_docx_txt or "", "Bilag_2_Prisskjema.docx")
            for r in ps_rows:
                write_price_schema_csv(matrix_dir, r["sheet"], r["headers"].split("|"), eval(r["constants"]))
            if p_terms:
                write_contract_terms_csv(matrix_dir, p_terms)
            rows.extend(rcP)
            if ps_rows:
                checks.append(Check(token="tender:price:schema_captured", ok=True, details=f"sheets={len(ps_rows)}", source=None))
        if ramme_txt:
            c_terms, c_req, rcC = extract_renhold_contract(ramme_txt, "Rammeavtale_Renholdstjenester.docx")
            if c_terms:
                write_contract_terms_csv(matrix_dir, c_terms)
                checks.append(Check(token="tender:contract:terms_extracted", ok=True, details=f"keys={len(c_terms)}", source=None))
            if c_req:
                write_requirements_matrix_csv(matrix_dir, c_req)
            rows.extend(rcC)
        if akrim_txt:
            a_terms, a_req, rcA = extract_renhold_akrim(akrim_txt, "Bilag_3_AKRIM_Renhold.docx")
            if a_terms:
                write_contract_terms_csv(matrix_dir, a_terms)
            if a_req:
                write_requirements_matrix_csv(matrix_dir, a_req)
            rows.extend(rcA)
        if selfrep_txt:
            s_terms, s_req, rcS = extract_renhold_akrim_selfreport(selfrep_txt, "Bilag_4_Egenrapportering_AKRIM_Renhold.docx")
            if s_terms:
                write_contract_terms_csv(matrix_dir, s_terms)
            if s_req:
                write_requirements_matrix_csv(matrix_dir, s_req)
            rows.extend(rcS)
        if exp_txt:
            e_req, rcE = extract_renhold_experience(exp_txt, "Vedlegg_2_Svarskjema_erfaring.docx")
            if e_req:
                write_requirements_matrix_csv(matrix_dir, e_req)
            rows.extend(rcE)

    receipts=os.path.join(proof_dir,"receipts.jsonl")
    root=os.path.join(proof_dir,"root.txt")
    write_receipts_and_root(receipts, root, rows)

    asset_id=f"tender:pack/{os.path.splitext(os.path.basename(args.tender_zip))[0]}"
    rec=build_decision("renhold-facility-digest", asset_id, token="ok", decision="allow", posture=args.posture, checks=checks, pack="tender-core", registry_sha=None)
    print(rec)
    print(rec["reason"])
    return 0

if __name__=="__main__":
    raise SystemExit(main())
