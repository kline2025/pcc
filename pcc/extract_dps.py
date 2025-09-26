import re
from typing import List, Dict, Tuple

def _fc(item, value, src, snip):
    return {"item": item, "value": value, "source_file": src, "source_snippet": snip}

def extract_dps_rules(text: str, src_file: str) -> Tuple[List[Dict], Dict, List[Dict], List[Dict]]:
    """
    Digdir – Kvalifikasjonsgrunnlag for DPS: 'Etablering og bruk av dynamisk innkjøpsordning'
    Returns: (forms_constraints_rows, terms_dict, requirements_rows, receipts)
    """
    t = text
    fc: List[Dict] = []
    terms: Dict[str, object] = {}
    req: List[Dict] = []
    rc: List[Dict] = []

    # Envelope / channel / language
    if re.search(r"\bMercell", t, re.I):
        fc.append(_fc("channel","Mercell",src_file,"Kommunikasjon via Mercell"))
    if re.search(r"Tilbud i konkurransene skal være utformet på norsk", t, re.I):
        fc.append(_fc("language","nb-NO",src_file,"Språk: norsk"))

    # DPS enablement and validity
    if re.search(r"dynamisk innkj[øo]psordning", t, re.I):
        terms["dps:enabled"] = True; rc.append({"type":"contract_term","key":"dps:enabled","value":True,"source_file":src_file})
    m = re.search(r"Innkj[øo]psordningen vil vare i\s*4\s*år", t, re.I)
    if m:
        terms["dps:validity_years"] = 4; rc.append({"type":"contract_term","key":"dps:validity_years","value":4,"source_file":src_file,"snippet":m.group(0)})

    # Establishment: first 30 days; rolling admission; processing time 10–15 wd
    if re.search(r"f[øo]rste kvalifikasjonsrunde.*30\s*dager", t, re.I):
        terms["dps:first_round_days"] = 30; rc.append({"type":"contract_term","key":"dps:first_round_days","value":30,"source_file":src_file})
    if re.search(r"fortl[øo]pende.*opptak", t, re.I):
        terms["dps:rolling_admission"] = True; rc.append({"type":"contract_term","key":"dps:rolling_admission","value":True,"source_file":src_file})
    if re.search(r"behandle s[øo]knad.*senest\s*10\s*virkedager", t, re.I):
        terms["dps:admission_processing_days"] = 10; rc.append({"type":"contract_term","key":"dps:admission_processing_days","value":10,"source_file":src_file})
    if re.search(r"forlenge.*til\s*15\s*virkedager", t, re.I):
        terms["dps:admission_processing_days_max"] = 15; rc.append({"type":"contract_term","key":"dps:admission_processing_days_max","value":15,"source_file":src_file})

    # Call-offs: invite all; min 10 days; best price-quality; eval at call-off
    if re.search(r"inviter[e]r.*alle\s+leverand[øo]rene.*tatt opp", t, re.I):
        terms["calloff:who_is_invited"] = "all_qualified"; rc.append({"type":"contract_term","key":"calloff:who_is_invited","value":"all_qualified","source_file":src_file})
    if re.search(r"Fristen.*ikke.*kortere enn\s*10\s*dager", t, re.I):
        terms["calloff:time_to_respond_days"] = 10; rc.append({"type":"contract_term","key":"calloff:time_to_respond_days","value":10,"source_file":src_file})
    if re.search(r"beste forholdet mellom pris og kvalitet", t, re.I):
        terms["calloff:award_rule"] = "best_price_quality"; rc.append({"type":"contract_term","key":"calloff:award_rule","value":"best_price_quality","source_file":src_file})
    terms["calloff:eval_at_calloff"] = True; rc.append({"type":"contract_term","key":"calloff:eval_at_calloff","value":True,"source_file":src_file})

    # Contracts used at call-off
    if re.search(r"SSA-B enkel", t, re.I): terms["calloff:contract:ssa_b_enkel"]=True; rc.append({"type":"contract_term","key":"calloff:contract:ssa_b_enkel","value":True,"source_file":src_file})
    if re.search(r"\bSSA-B\b", t, re.I):  terms["calloff:contract:ssa_b"]=True;     rc.append({"type":"contract_term","key":"calloff:contract:ssa_b","value":True,"source_file":src_file})
    if re.search(r"\bSSA-O\b", t, re.I):  terms["calloff:contract:ssa_o"]=True;     rc.append({"type":"contract_term","key":"calloff:contract:ssa_o","value":True,"source_file":src_file})
    if re.search(r"Databehandleravtale vil inng[åa]s", t, re.I):
        terms["privacy:dpa_required_at_calloff"]=True; rc.append({"type":"contract_term","key":"privacy:dpa_required_at_calloff","value":True,"source_file":src_file})

    # Admission documentation (ESPD + eBevis)
    if re.search(r"ESPD", t, re.I):
        req.append({"req_id":"DPS-ESPD","section":"Opptak","kind":"mandatory","prompt_kind":"attachment",
                    "value_hint":"ESPD i Mercell","krav_text":"Lever ESPD-skjema (egenerklæring) i Mercell for opptak.",
                    "source_file":src_file,"source_row":"ESPD"})
    if re.search(r"eBevis", t, re.I):
        terms["dps:uses_ebevis"]=True; rc.append({"type":"contract_term","key":"dps:uses_ebevis","value":True,"source_file":src_file})

    # EHF invoicing (generic state requirement)
    if re.search(r"elektronisk.*faktura.*EHF", t, re.I):
        terms["invoice:ehf_required"]=True; rc.append({"type":"contract_term","key":"invoice:ehf_required","value":True,"source_file":src_file})

    return fc, terms, req, rc
