import argparse, os, zipfile
from .version import VERSION
from .bedrock import build_decision, Check
from .merkle import write_receipts_and_root
from .matrix import write_forms_constraints_csv, write_submission_checklist_csv, write_criteria_and_formula_csv, write_price_schema_csv, write_requirements_matrix_csv, write_contract_terms_csv
from .extract_ns8407_total import extract_itt_total, extract_price_form, extract_avtale_total, extract_tebok_total
from .extract_ns8407_specs import extract_funksjonsprogram, extract_uu_plan
from .extract_ns8407_bim_mop import extract_bim, extract_mop
from .extract_ns8407_sha import extract_sha_plan

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
        itt_txt,_   = _read(z, ["IIA1 Tilbudsinvitasjon - Totalentreprise - Anbudskonkurranse.txt","IIA1_Tilbudsinvitasjon.txt","Konkurransebestemmelser.txt"])
        pris_txt,_  = _read(z, ["IIA2 Totalentreprise tilbudsskjema.txt","IIA2_Tilbudsskjema.txt","Tilbudsskjema.txt"])
        avt_txt,_   = _read(z, ["IIA3 Utkast til avtaledokument for totalentreprise.txt","IIA3_Avtaledokument.txt","Avtaledokument.txt"])
        tebok_txt,_ = _read(z, ["IIA4 Totalentrepriseboka.txt","IIA4_TEBOK.txt","TEBOK.txt"])
        funks_txt,_ = _read(z, ["Vedlegg 01-01 Funksjonsprogram.txt","Funksjonsprogram.txt"]) 
        uu_txt,_     = _read(z, ["Vedlegg 01-09 Tverrfaglig oppfølgingsplan universell utforming.txt","UU-oppfølgingsplan.txt"]) 
        bep_txt,_    = _read(z, ["Vedlegg 08-02 Mal for BIM-gjennomføringsplan.txt","BEP.txt"]) 
        eir_txt,_    = _read(z, ["Vedlegg 08-01 Krav til informasjonsutveksling for BIM.txt","EIR.txt"]) 
        simba_txt,_  = _read(z, ["Vedlegg 08-03 SIMBA 2.1 Generelle krav.txt","SIMBA.txt"]) 
        mop_txt,_    = _read(z, ["Vedlegg 02-01 Miljøoppfølgingsplan (MOP).txt","MOP.txt"]) 
        mopv_txt,_   = _read(z, ["Vedlegg 02-02 Veiledning til MP og MOP for Nordre Follo kommune.txt","MOP_veileder.txt"]) 
        sha_txt,_    = _read(z, ["IIS2 SHA-plan.txt","SHA-plan.txt","IIS2_SHA_plan.txt"]) 
        frrut_txt,_  = _read(z, ["IIS8 Forretningsrutiner i byggefasen Totalentreprise (NS 8407).txt","Forretningsrutiner_NS8407.txt"])

        if itt_txt:
            fc, subm, cf, req, rc = extract_itt_total(itt_txt, "IIA1_Tilbudsinvitasjon.pdf")
            if fc: write_forms_constraints_csv(matrix_dir, fc)
            if subm: write_submission_checklist_csv(matrix_dir, subm)
            if cf: write_criteria_and_formula_csv(matrix_dir, cf)
            if req: write_requirements_matrix_csv(matrix_dir, req)
            rows.extend(rc)
            if any(r for r in cf if r.get("group")=="price"): checks.append(Check(token="tender:criteria:formula_disclosed", ok=True, details="linear lowest=10; ≥2x=0", source=None))

        if pris_txt:
            ps_rows, rc2 = extract_price_form(pris_txt, "IIA2_Tilbudsskjema.pdf")
            for r in ps_rows:
                write_price_schema_csv(matrix_dir, r["sheet"], r["headers"].split("|"), eval(r["constants"]))
            rows.extend(rc2)
            if ps_rows: checks.append(Check(token="tender:price:schema_captured", ok=True, details=f"sheets={len(ps_rows)}", source=None))

        terms={}
        if avt_txt:
            t1, rc3, req2 = extract_avtale_total(avt_txt, "IIA3_Avtaledokument.pdf")
            terms.update(t1); rows.extend(rc3)
            if req2: write_requirements_matrix_csv(matrix_dir, req2)
        if tebok_txt:
            t2, rc4, req3 = extract_tebok_total(tebok_txt, "IIA4_TEBOK.pdf")
            terms.update(t2); rows.extend(rc4)
            if req3: write_requirements_matrix_csv(matrix_dir, req3)
        if terms:
            write_contract_terms_csv(matrix_dir, terms)
            checks.append(Check(token="tender:contract:terms_extracted", ok=True, details=f"keys={len(terms)}", source=None))

    receipts=os.path.join(proof_dir,"receipts.jsonl")
    root=os.path.join(proof_dir,"root.txt")
    write_receipts_and_root(receipts, root, rows)

    asset_id=f"tender:pack/{os.path.splitext(os.path.basename(args.tender_zip))[0]}"
    record=build_decision("ns8407-total-digest", asset_id, token="ok", decision="allow", posture=args.posture, checks=checks, pack="tender-core", registry_sha=None)
    print(record)
    print(record["reason"])
    return 0

if __name__=="__main__":
    raise SystemExit(main())
