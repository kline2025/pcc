import argparse, os, zipfile
from .bedrock import build_decision, Check
from .merkle import write_receipts_and_root
from .matrix import (
    write_forms_constraints_csv, write_submission_checklist_csv,
    write_criteria_and_formula_csv, write_contract_terms_csv, write_requirements_matrix_csv, write_price_schema_csv, write_requirements_matrix_csv
)
from .extract_ssa_v import extract_ssa_v_itt, extract_ssa_v_contract, extract_ssa_v_sla, extract_ssa_v_dpa, extract_ssa_v_spec, extract_ssa_v_price_schema, extract_ssa_v_service_access, extract_ssa_v_platform

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
        itt_txt,_ = _read(z, ["Konkurransebestemmelser.txt",
                              "a. Konkurransebestemmelser.txt",
                              "Document-3.txt"])
        ssa_txt,_ = _read(z, ["SSA-V_generell_avtaletekst.txt",
                              "SSA-V_generell_avtaletekst_2024.txt",
                              "j. SSA-V_generell_avtaletekst_2024 (3).txt"])

        sla_txt,_ = _read(z, [
            "k. SSA-V _bilag_2024 Service Manager.txt",
            "SSA-V_bilag_2024_Service_Manager.txt",
            "SSAV_Bilag5_SLA.txt"
        ])
        dpa_txt,_ = _read(z, [
            "l. Standard databehandleravtale - utfylt av Kunde.txt",
            "Standard_databehandleravtale_utfylt.txt",
            "DPA.txt"
        ])

        if itt_txt:
            fc, chk, cf, rc = extract_ssa_v_itt(itt_txt, "Konkurransebestemmelser.pdf")
            if fc:  write_forms_constraints_csv(matrix_dir, fc)
            if chk: write_submission_checklist_csv(matrix_dir, chk)
            if cf:  write_criteria_and_formula_csv(matrix_dir, cf)
            rows.extend(rc)
            if cf: checks.append(Check(token="tender:criteria:weights_disclosed", ok=True, details=f"{len(cf)} rows", source=None))

        if ssa_txt:
            terms, req, rc2 = extract_ssa_v_contract(ssa_txt, "SSA-V_generell_avtaletekst_2024.docx")
            if terms: write_contract_terms_csv(matrix_dir, terms)
            rows.extend(rc2)
            checks.append(Check(token="tender:contract:family", ok=True, details="SSA-V", source=None))
            if terms.get("sla:bilag5_required"): checks.append(Check(token="tender:sla:bilag5_required", ok=True, details="Bilag 5", source=None))
            if terms.get("privacy:dpa_required"): checks.append(Check(token="tender:privacy:dpa_required", ok=True, details="Bilag 11", source=None))
        if sla_txt:
            sla_terms, sla_req, sla_rc = extract_ssa_v_sla(sla_txt, "SSA-V_Bilag5_SLA.docx")
            if sla_terms: write_contract_terms_csv(matrix_dir, sla_terms)
            if sla_req:   write_requirements_matrix_csv(matrix_dir, sla_req)
            rows.extend(sla_rc)
        if dpa_txt:
            dpa_terms, dpa_req, dpa_rc = extract_ssa_v_dpa(dpa_txt, "DPA_utfylt_av_kunde.docx")
            if dpa_terms: write_contract_terms_csv(matrix_dir, dpa_terms)
            if dpa_req:   write_requirements_matrix_csv(matrix_dir, dpa_req)
            rows.extend(dpa_rc)
        if spec_txt:
            r_rows, r_rc = extract_ssa_v_spec(spec_txt, "Kravspesifikasjon_Service_Manager.pdf")
            if r_rows:
                write_requirements_matrix_csv(matrix_dir, r_rows)
            rows.extend(r_rc)
        if price_txt:
            ps_rows, ps_rc = extract_ssa_v_price_schema(price_txt, "Prisskjema_Service_Manager.pdf")
            for r in ps_rows:
                write_price_schema_csv(matrix_dir, r["sheet"], r["headers"], r["constants"])
            rows.extend(ps_rc)
        if svcacc_txt:
            sa_terms, sa_req, sa_rc = extract_ssa_v_service_access(svcacc_txt, "Servicetilgangsavtale_Avtalemal.docx")
            if sa_terms: write_contract_terms_csv(matrix_dir, sa_terms)
            if sa_req:   write_requirements_matrix_csv(matrix_dir, sa_req)
            rows.extend(sa_rc)
        if platform_txt:
            pf_terms, pf_req, pf_rc = extract_ssa_v_platform(platform_txt, "Kundens_tekniske_plattform.docx")
            if pf_terms: write_contract_terms_csv(matrix_dir, pf_terms)
            if pf_req:   write_requirements_matrix_csv(matrix_dir, pf_req)
            rows.extend(pf_rc)

    receipts = os.path.join(proof_dir, "receipts.jsonl")
    root     = os.path.join(proof_dir, "root.txt")
    write_receipts_and_root(receipts, root, rows)

    asset_id = f"tender:pack/{os.path.splitext(os.path.basename(args.tender_zip))[0]}"
    record = build_decision("ssa-v-digest", asset_id, token="ok", decision="allow",
                            posture=args.posture, checks=checks, pack="tender-core", registry_sha=None)
    print(record)
    print(record["reason"])
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
