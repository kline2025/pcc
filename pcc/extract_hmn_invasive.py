import re
from typing import List, Dict, Tuple

def _norm_date(s: str) -> str:
    s = s.replace('.', '-').replace('/', '-').strip()
    p = s.split('-')
    if len(p) == 3:
        d, m, y = p
        if len(y) == 2: y = '20' + y
        return f"{y.zfill(4)}-{m.zfill(2)}-{d.zfill(2)}"
    return s

def _fc(item, value, file, snip):
    return {"item": item, "value": value, "source_file": file, "source_snippet": snip}

def extract_itt(text: str, src_file: str):
    fc = []; subm = []; cf = []; rc = []
    t = text

    if re.search(r'\bmercell\b', t, re.I): fc.append(_fc("channel","Mercell",src_file,"Mercell"))
    if re.search(r'skrevet på norsk|språk[:\s]*norsk', t, re.I): fc.append(_fc("language","nb-NO",src_file,"norsk"))
    m = re.search(r'filnavn[^.\n]{0,60}40\s*tegn', t, re.I)
    if m: fc.append(_fc("filename_limit_chars", 40, src_file, m.group(0)))
    m = re.search(r'(bindende|vedståelsesfrist)[^\n]{0,40}(\d{1,2})\s*måneder', t, re.I)
    if m: fc.append(_fc("bid_validity_months", int(m.group(2)), src_file, m.group(0)))
    if re.search(r'alternative tilbud\s+aksepteres\s+ikke', t, re.I): fc.append(_fc("alt_offers_allowed", False, src_file, "Alternative tilbud aksepteres ikke"))
    if re.search(r'parallelle tilbud\s+aksepteres\s+ikke', t, re.I): fc.append(_fc("parallel_offers_allowed", False, src_file, "Parallelle tilbud aksepteres ikke"))
    if re.search(r'\bespd\b', t, re.I): fc.append(_fc("espd_required", True, src_file,"ESPD"))
    if re.search(r'\bebevis\b', t, re.I): fc.append(_fc("ebevis_used", True, src_file,"eBevis"))
    if re.search(r'ikke\s*inndelt\s*i\s*delkontrakter|ikke\s*delkontrakter', t, re.I): fc.append(_fc("lots","No (ikke delkontrakter)",src_file,"ikke delkontrakter"))
    if re.search(r'rammeavtale[^.\n]{0,20}én leverandør', t, re.I): fc.append(_fc("contract_type","Rammeavtale med én leverandør",src_file,"Rammeavtale … én leverandør"))
    m = re.search(r'oppstart[^0-9]{0,20}([0-3]?\d[./-][01]?\d[./-]\d{2,4})', t, re.I)
    if m: fc.append(_fc("start_of_contract", _norm_date(m.group(1)), src_file, m.group(0)))
    if re.search(r'vareprøv', t, re.I): fc.append(_fc("samples_required_for_evaluation", True, src_file, "Vareprøver"))
    m = re.search(r'ddp[^.\n]{0,40}10\s*(arbeids|virke)dag', t, re.I)
    if m: fc.append(_fc("clinical_trial_samples_ddp_days", 10, src_file, m.group(0)))
    m = re.search(r'kvalitetsscore\s*([0-9])\s*eller\s*lavere\s*vil\s*.*avvis', t, re.I)
    if m: fc.append(_fc("quality_min_score_reject_threshold", int(m.group(1)), src_file, m.group(0)))

    for code,title in [
        ("Vedlegg 1","Tilbudsbrev"),
        ("Vedlegg 2","Kravspesifikasjon (utfylt)"),
        ("Vedlegg 3","Prisskjema (utfylt)"),
        ("Vedlegg 4","Bruksanvisning og begrunnelse for sladding"),
        ("Vedlegg 5","Sladdet versjon av tilbudet"),
        ("Vedlegg 6","Utfylt miljøskjema"),
        ("Vedlegg 7","Egenerklæring om russisk involvering"),
        ("Vedlegg 8","Krav ved risiko for brudd på folkeretten"),
        ("Vedlegg 9","Forpliktelseserklæring"),
        ("Vedlegg 10","Morselskapsgaranti"),
        ("Vedlegg 11","Annet vedlegg")
    ]:
        if re.search(code, t, re.I):
            subm.append({"doc_code":code, "title":title, "phase":"Offer", "mandatory": True if "hvis" not in title.lower() and "annet" not in title.lower() else False, "source_file":src_file, "snippet":code+" "+title})

    weights = []; tot = None
    if re.search(r'pris[^%\n]{0,15}40\s*%', t, re.I): weights.append(("Pris",40))
    if re.search(r'kvalitet[^%\n]{0,15}60\s*%', t, re.I): weights.append(("Kvalitet",60))
    tot = sum(p for _,p in weights) if weights else None
    for name,p in weights:
        cf.append({"criterion":name,"weight_pct":p,"group":"price" if name.lower()=="pris" else "quality","total_pct":tot or "",
                   "price_model":"prisskjema_proportional" if name.lower()=="pris" else "",
                   "scoring_model":"poeng=10*(laveste/evaluert)" if name.lower()=="pris" else "0–10 fagpanel",
                   "model_anchor":"Prisskjema (HF 30% / LS 70%)" if name.lower()=="pris" else "ITT/Kravspesifikasjon"})
    if tot is not None: rc.append({"type":"award_weights_total","total_pct":tot,"source_file":src_file})

    if re.search(r'HF\s*30\s*%\s*/\s*LS\s*70\s*%', t, re.I):
        rc.append({"type":"price_weight_split","details":"HF 30% / LS 70%","source_file":src_file})

    return fc, subm, cf, rc

def extract_spec(text: str, src_file: str):
    rows = []; rc = []
    add = rows.append
    def R(id,sec,kind,pk,hint,txt):
        add({"req_id":id,"section":sec,"kind":kind,"prompt_kind":pk,"value_hint":hint,"krav_text":txt,"source_file":src_file,"source_row":id})

    if re.search(r'ce-?merket', text, re.I): R("G.2","Generelle krav","mandatory","boolean","","CE-merket iht. gjeldende regelverk; samsvarserklæring på forespørsel.")
    if re.search(r'produktdatablad|brosjyre', text, re.I): R("G.3","Generelle krav","mandatory","attachment","","Produktdatablad/brosjyre vedlegges for alle produkter.")
    if re.search(r'merking|etikett', text, re.I): R("G.6","Generelle krav","mandatory","boolean","","Tydelig merking av emballasje (art.nr, batch/lot, str./dim., utløp, antall).")
    m = re.search(r'steril[a-z ]*holdbarhet[^0-9]{0,10}(\d{1,3})\s*mån', text, re.I)
    R("G.8","Generelle krav","mandatory","value","≥12 måneder", "Oppgi steril holdbarhet (≥ 12 måneder).")
    if re.search(r'utfasingsliste|svhc|europeisk utfasingsliste', text, re.I): R("G.12","Generelle krav","mandatory","value","","Oppgi ev. stoffer på europeisk utfasingsliste (>0,1 %).")
    if re.search(r'300\s*mmhg', text, re.I): R("1.1","Delkontrakt 1","mandatory","value","300 mmHg; ml/t ved 300 mmHg","Settene skal tåle 300 mmHg; oppgi gjennomstrømning ved 300 mmHg.")
    if re.search(r'15\s*µm|15\s*um', text, re.I): R("1.3","Delkontrakt 1","mandatory","boolean","≤15 µm","Partikkelfilter maks 15 µm.")
    if re.search(r'72\s*t', text, re.I): R("1.6","Delkontrakt 1","mandatory","value","≥72 timer","Oppgi skiftfrekvens for alle sett-varianter (min. 72 t).")
    if re.search(r'klorhexidin|klorheksidin', text, re.I): R("1.10","Delkontrakt 1","mandatory","mixed","klorhexidin 5 mg/ml","Port tåler klorhexidin 5 mg/ml; oppgi perforasjoner/rengjøring.")
    if re.search(r'kompatibel.*philips|ge|mindray', text, re.I): R("1.16","Delkontrakt 1","mandatory","boolean","","Trykkabler kompatible med monitorer (Philips/GE/Mindray).")
    return rows, rc

def extract_price(text: str, src_file: str):
    const = {}; receipts = []
    if re.search(r'HF\s*30\s*%\s*/\s*LS\s*70\s*%', text, re.I):
        const["hf_weight_pct"]=30; const["ls_weight_pct"]=70
        receipts.append({"type":"price_constant","key":"hf_ls_split","value":"30/70","source_file":src_file})
    if re.search(r'vareprøve', text, re.I):
        const["sample_flag_column"]=True
        receipts.append({"type":"price_schema_note","key":"sample_flag_column","value":True,"source_file":src_file})
    return const, receipts

def extract_contract(text: str, src_file: str):
    terms = {}; rc = []
    t = text
    if re.search(r'maksimal.*6\s*år', t, re.I): terms["contract:period:max_years"]=6
    if re.search(r'forlenges[^.\n]*2\s*år', t, re.I): terms["contract:period:extension_step"]=2
    if re.search(r'prøvetid[^.\n]*6\s*mån', t, re.I): terms["contract:probation_months"]=6
    if re.search(r'30\s*dagers\s*varsel', t, re.I): terms["contract:probation_termination_notice_days"]=30
    if re.search(r'6\s*måneder\s*varsel', t, re.I): terms["contract:termination_notice_months"]=6
    if re.search(r'ddp[^.\n]*2020', t, re.I): terms["delivery:incoterms"]="DDP_Incoterms2020"
    if re.search(r'elektronisk\s+varekatalog', t, re.I): terms["catalog:electronic_required"]=True
    if re.search(r'katalog[^.\n]*dagmulkt[^.\n]*500', t, re.I): terms["catalog:delay_ld_nok_per_working_day"]=500
    if re.search(r'kvartalsvis\s+statistikk', t, re.I): terms["stats:quarterly_due_dates"]="Q1 20.04; Q2 05.08; Q3 20.10; Q4 20.01"
    if re.search(r'statistikk[^.\n]*dagmulkt[^.\n]*1\s*000', t, re.I): terms["stats:delay_ld_nok_per_working_day"]=1000
    if re.search(r'prisene\s+er\s+faste\s+i\s+12\s*mån', t, re.I): terms["price:fixed_first_months"]=12
    if re.search(r'2\s*%', t, re.I) and re.search(r'ekstraordinær|myndighet', t, re.I): terms["price:authority_change_threshold_pct"]=2
    if re.search(r'I44', t, re.I): terms["price:fx_index"]="I44_importveid"
    if re.search(r'valuta[^.\n]*60\s*%', t, re.I): terms["price:fx_share_pct"]=60
    if re.search(r'én\s*gang\s*per\s*år', t, re.I): terms["price:fx_adjust_freq"]="1"
    if re.search(r'varsles[^.\n]*2\s*måneder', t, re.I): terms["price:kpi_first_notice_weeks"]=8
    if re.search(r'førstegangs[^.\n]*40\s*%', t, re.I): terms["price:kpi_first_fraction_pct"]=40
    if re.search(r'justeres[^.\n]*2\s*måneder\s+etter', t, re.I): terms["price:kpi_late_notice_effect_months"]=2
    if re.search(r'betalingsfrist\s*er\s*30\s*dager', t, re.I): terms["payment:days"]=30
    if re.search(r'ikke\s*beregnes\s+.*gebyr[^.\n]*fakturer', t, re.I): terms["invoice:fee_prohibited"]=True
    if re.search(r'gebyr[^.\n]*500\s*pr\s*faktura', t, re.I): terms["invoice:misbilling_fee_nok"]=500
    if re.search(r'dagmulkt[^.\n]*0[,\.]?25\s*%\s*per\s*virkedag', t, re.I): terms["delay:ld_rate_pct_per_working_day"]=0.25
    if re.search(r'eller\s*kr\s*500', t, re.I): terms["delay:ld_min_nok_per_day"]=500
    if re.search(r'begrenset\s*til\s*100\s*virkedager', t, re.I): terms["delay:ld_max_working_days"]=100
    if re.search(r'force majeure[^.\n]*75\s*kalenderdager', t, re.I): terms["force_majeure:termination_days"]=75
    if re.search(r'15\s*kalenderdagers\s*varsel', t, re.I): terms["force_majeure:notice_days"]=15
    if re.search(r'bot[^.\n]*0[,\.]?2\s*%\s*.*10\s*000', t, re.I):
        terms["marketing:penalty_pct"]=0.2; terms["marketing:penalty_min_nok"]=10000
    for k,v in terms.items():
        rc.append({"type":"contract_term","key":k,"value":v,"source_file":src_file})
    return terms, rc
