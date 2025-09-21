import re
from typing import List, Dict, Tuple

def _fc(item, value, src, snip):
    return {"item": item, "value": value, "source_file": src, "source_snippet": snip}

def _norm_date_ddmmyyyy(s: str) -> str:
    m = re.search(r"(\d{2})[./-](\d{2})[./-](\d{4})", s)
    if not m:
        return s.strip()
    d, mn, y = m.groups()
    return f"{y}-{mn}-{d}"

def _int_nok(s: str) -> int:
    # 35 millioner -> 35000000, "180 mill" -> 180000000
    s = s.replace("\u00a0"," ").lower()
    m = re.search(r"([0-9][0-9 .]*)\s*(mill(?:ion)?|m)", s)
    if m:
        n = int(re.sub(r"[ .]", "", m.group(1)))
        return n * 1_000_000
    m = re.search(r"([0-9][0-9 .]*)", s)
    return int(re.sub(r"[ .]", "", m.group(1))) if m else 0

def extract_office_itt(text: str, src_file: str) -> Tuple[List[Dict], List[Dict], List[Dict], Dict, List[Dict]]:
    """
    Returns:
      forms_constraints_rows, submission_checklist_rows, criteria_rows, contract_terms (dict), receipts (list)
    Grounded in 'Konkurransebestemmelser – kontorrekvisita og batterier'.
    """
    t = text
    fc: List[Dict] = []
    chk: List[Dict] = []
    cf: List[Dict] = []
    TERMS: Dict[str, object] = {}
    RC: List[Dict] = []

    # ---- Envelope / process ----
    if re.search(r"\båpen\s+anbudskonkurranse\b", t, re.I):
        fc.append(_fc("procedure","Åpen anbudskonkurranse (del I og III); uten forhandling", src_file, "åpen anbudskonkurranse"))
    if re.search(r"\bmercell", t, re.I):
        fc.append(_fc("channel","Mercell", src_file, "Kommunikasjon via Mercell"))
    if re.search(r"språk[:\s]*(norsk|nb|bokm[aå]l)", t, re.I):
        fc.append(_fc("language","nb-NO", src_file, "Språk"))
    if re.search(r"filnavn[^.\n]{0,40}40\s*tegn", t, re.I):
        fc.append(_fc("filename_limit_chars",40, src_file, "≤ 40 tegn"))
    if re.search(r"alternative\s+tilbud\s+aksepteres\s+ikke", t, re.I):
        fc.append(_fc("alt_offers_allowed", False, src_file, "Alternative tilbud aksepteres ikke"))
    if re.search(r"ett\s+tilbud\s+per\s+delkontrakt", t, re.I):
        fc.append(_fc("parallel_offers_allowed", False, src_file, "Kun ett tilbud per delkontrakt"))
        TERMS["lots:offer_per_lot"] = True; RC.append({"type":"contract_term","key":"lots:offer_per_lot","value":True,"source_file":src_file})
    m = re.search(r"vedst[åa]elsesfrist[^0-9]{0,30}(\d{1,2})\s*m[åa]neder", t, re.I)
    if m:
        fc.append(_fc("bid_validity_months", int(m.group(1)), src_file, m.group(0)))

    # ---- Lots ----
    if re.search(r"delkontrakter?\s*[:\-]?\s*2", t, re.I):
        fc.append(_fc("lots_count", 2, src_file, "Delkontrakter: 2"))
        TERMS["lots:count"] = 2; RC.append({"type":"contract_term","key":"lots:count","value":2,"source_file":src_file})

    if re.search(r"delkontrakt\s*1.*kontorrekvisita", t, re.I) and re.search(r"delkontrakt\s*2.*batterier", t, re.I|re.S):
        names = "Kontorrekvisita|Batterier"
        fc.append(_fc("lots_names", names, src_file, "Delkontrakt 1/2"))
        TERMS["lots:names"] = names; RC.append({"type":"contract_term","key":"lots:names","value":names,"source_file":src_file})

    # Values & maxima
    m = re.search(r"kontorrekvisita[^.\n]*?([0-9][0-9 .]*\s*mill)", t, re.I)
    if m:
        v = _int_nok(m.group(1)); fc.append(_fc("estimated_annual_value_lot1_nok", v, src_file, m.group(0)))
    m = re.search(r"batterier[^.\n]*?([0-9][0-9 .]*\s*mill)", t, re.I)
    if m:
        v = _int_nok(m.group(1)); fc.append(_fc("estimated_annual_value_lot2_nok", v, src_file, m.group(0)))
    m1 = re.search(r"kontorrekvisita[^.\n]*maksimale[^.\n]*?([0-9][0-9 .]*\s*mill)", t, re.I)
    if m1:
        TERMS["max_value_lot1_nok"] = _int_nok(m1.group(1)); RC.append({"type":"contract_term","key":"max_value_lot1_nok","value":TERMS["max_value_lot1_nok"],"source_file":src_file})
    m2 = re.search(r"batterier[^.\n]*maksimale[^.\n]*?([0-9][0-9 .]*\s*mill)", t, re.I)
    if m2:
        TERMS["max_value_lot2_nok"] = _int_nok(m2.group(1)); RC.append({"type":"contract_term","key":"max_value_lot2_nok","value":TERMS["max_value_lot2_nok"],"source_file":src_file})

    # Period / extensions
    if re.search(r"gjelder i\s*2\s*år", t, re.I):
        fc.append(_fc("contract_period_base_years", 2, src_file, "Avtalen gjelder i 2 år"))
    if re.search(r"maksimal[et]? samlet avtaleperiode.*4\s*år", t, re.I):
        fc.append(_fc("contract_period_max_years", 4, src_file, "Maksimal samlet 4 år"))
    if re.search(r"forlenge.*1\s*år\s*om gangen", t, re.I):
        fc.append(_fc("extension_step_years", 1, src_file, "Forlengelse 1 år om gangen"))

    # Important dates
    qm = re.search(r"Frist for [åa] stille sp[øo]rsm[åa]l[^0-9]{0,20}(\d{2}[./-]\d{2}[./-]\d{4})", t, re.I)
    if qm: fc.append(_fc("question_deadline", _norm_date_ddmmyyyy(qm.group(1)), src_file, qm.group(0)))
    om = re.search(r"Frist for [åa] levere tilbud[^0-9]{0,40}(\d{2}[./-]\d{2}[./-]\d{4})", t, re.I)
    if om: fc.append(_fc("offer_deadline", _norm_date_ddmmyyyy(om.group(1)) + " 00:00", src_file, om.group(0)))
    cm = re.search(r"Oppstart av avtale[^0-9]{0,20}(\d{2}[./-]\d{2}[./-]\d{4})", t, re.I)
    if cm: fc.append(_fc("contract_start", _norm_date_ddmmyyyy(cm.group(1)), src_file, cm.group(0)))

    # ESPD / eBevis
    if re.search(r"\bESPD\b", t, re.I):
        fc.append(_fc("espd_required", True, src_file, "ESPD i Mercell"))
    if re.search(r"\beBevis\b", t, re.I):
        fc.append(_fc("ebevis_used", True, src_file, "eBevis"))

    # ---- Checklist table (3.2) ----
    must = [
        ("Bilag 15", "Tilbudsbrev (PDF)"),
        ("Bilag 2",  "Kravspesifikasjon (Excel)"),
        ("Bilag 1",  "Prisskjema (Excel)"),
        ("Bilag 12", "Bruksanvisning og begrunnelse for sladding (PDF)"),
        ("Bilag 19", "Sladdet versjon av tilbudet (PDF)"),
        ("Bilag 17", "Svarskjema erfaring (PDF)"),
        ("Bilag 14", "Egenerklæring om russisk involvering (PDF)")
    ]
    opt = [
        ("Bilag 5", "Forpliktelseserklæring (PDF)"),
        ("Bilag 16","Morselskapsgaranti (PDF)")
    ]
    for code, title in must:
        if re.search(re.escape(code), t, re.I):
            chk.append({"doc_code":code,"title":title,"phase":"Offer","mandatory":True,"source_file":src_file,"snippet":code})
    for code, title in opt:
        if re.search(re.escape(code), t, re.I):
            chk.append({"doc_code":code,"title":title,"phase":"Offer","mandatory":False,"source_file":src_file,"snippet":code})

    # ---- Criteria & price model (6.1–6.4) ----
    # Lot 1: Pris 70, Miljø 30
    if re.search(r"Delkontrakt\s*1.*Pris[^%]{0,10}70\s*%.*Milj[øo][^%]{0,10}30\s*%", t, re.I|re.S):
        cf.append({"criterion":"Pris (Lot 1 Kontorrekvisita)","weight_pct":70,"group":"price","total_pct":100,
                   "price_model":"proportional","scoring_model":"lowest total = 10; others proportionally","model_anchor":"Bilag 1 – prisskjema / pkt. 6.2"})
        cf.append({"criterion":"Miljø (Lot 1 Kontorrekvisita)","weight_pct":30,"group":"quality","total_pct":100,
                   "price_model":"","scoring_model":"absolutt 0–10 (Type-I = 10 poeng)","model_anchor":"Kravspesifikasjon / pkt. 6.4"})
        TERMS["award:lot1:price_weight_pct"] = 70; RC.append({"type":"contract_term","key":"award:lot1:price_weight_pct","value":70,"source_file":src_file})
        TERMS["award:lot1:quality_weight_pct"] = 30; RC.append({"type":"contract_term","key":"award:lot1:quality_weight_pct","value":30,"source_file":src_file})

    # Lot 2: Pris 50, Kvalitet 20, Miljø 30
    if re.search(r"Delkontrakt\s*2.*Pris[^%]{0,10}50\s*%.*Kvalitet[^%]{0,10}20\s*%.*Milj[øo][^%]{0,10}30\s*%", t, re.I|re.S):
        cf.append({"criterion":"Pris (Lot 2 Batterier)","weight_pct":50,"group":"price","total_pct":100,
                   "price_model":"proportional","scoring_model":"lowest total = 10; others proportionally","model_anchor":"Bilag 1 – prisskjema / pkt. 6.2"})
        cf.append({"criterion":"Kvalitet (Lot 2 Batterier)","weight_pct":20,"group":"quality","total_pct":100,
                   "price_model":"","scoring_model":"normalisert 0–10 mot beste tilbud","model_anchor":"Kravspesifikasjon / pkt. 6.3"})
        cf.append({"criterion":"Miljø (Lot 2 Batterier)","weight_pct":30,"group":"quality","total_pct":100,
                   "price_model":"","scoring_model":"absolutt 0–10 (Type-I = 10 poeng)","model_anchor":"Kravspesifikasjon / pkt. 6.4"})
        TERMS["award:lot2:price_weight_pct"] = 50; RC.append({"type":"contract_term","key":"award:lot2:price_weight_pct","value":50,"source_file":src_file})
        TERMS["award:lot2:quality_weight_pct"] = 50; RC.append({"type":"contract_term","key":"award:lot2:quality_weight_pct","value":50,"source_file":src_file})

    # Price evaluation: proportional 10-point model; basket (+10% tilleggs-sortiment); volume rebate weights HSØ 30% / others 5%
    if re.search(r"lavest\s+totalsum\s+gis\s*10\s+poeng", t, re.I):
        TERMS["price:eval_method"] = "proportional_lowest_max10"; RC.append({"type":"contract_term","key":"price:eval_method","value":"proportional_lowest_max10","source_file":src_file})
    if re.search(r"tilleggs?sortiment.*10\s*%", t, re.I):
        TERMS["price:cart_formula"] = "cart = Σ(p_i×vol_i) + 10%×(1+avg_markup)"; RC.append({"type":"contract_term","key":"price:cart_formula","value":TERMS["price:cart_formula"],"source_file":src_file})
    m = re.search(r"volumrabatt.*HS[øo]?\s*30\s*%.*(?:øvrige|andre)\s*5\s*%", t, re.I)
    if m:
        TERMS["price:volume_discount_weights"] = "HSØ 30% | øvrige 5%"; RC.append({"type":"contract_term","key":"price:volume_discount_weights","value":"HSØ 30% | øvrige 5%","source_file":src_file})
    if re.search(r"ikke\s+anledning\s+til\s+å\s+tilby\s+samme\s+artikkel.*ulike\s+priser", t, re.I):
        TERMS["product:duplicate_price_disallowed"] = True; RC.append({"type":"contract_term","key":"product:duplicate_price_disallowed","value":True,"source_file":src_file})

    # Samples (Lot 1)
    if re.search(r"varepr[øo]ver.*kontorrekvisita", t, re.I):
        TERMS["samples:lot1_required"] = True; RC.append({"type":"contract_term","key":"samples:lot1_required","value":True,"source_file":src_file})

    # Return the sets
    return fc, chk, cf, TERMS, RC


# ---------------- Prisskjema (Bilag 1) — multi-lot office/batteries ----------------
def extract_office_price_schema(text: str, src_file: str):
    '''
    Returns (sheet_rows, receipts):
      sheet_rows: list of dicts {sheet, headers (list), constants (dict)}
      receipts: list of proof rows
    sheet_rows will be written by write_price_schema_csv(sheet, headers, constants)
    '''
    t = text
    rows = []
    rc   = []

    # Detect lots present in prisskjema (page 6 shows the "Omfang" table with names)
    lot1 = bool(re.search(r"Delkontrakt\s*1\s*Kontorrekvisita", t, re.I))
    lot2 = bool(re.search(r"Delkontrakt\s*2\s*Batterier", t, re.I))

    # Canonical column headers (as seen on page 7 and repeated)
    common_headers = [
        "Linjenr.","Kategorinivå 1","Kategorinivå 2","Oppdragsgivers beskrivelse (anbudslinjenavn)",
        "Referansevare","Varianter","Antatt mengde pr. år","Enhet",
        "Antatt mengde EV-enheter","EV-enhet","Tilbyders art.nr","Tilbyders artikkelnavn",
        "Kort beskrivelse av og/eller kommentar til tilbudt produkt",
        "Minste salgsenhet","Antall minste enhet per salgsenhet",
        "Enhet for utfylling av antall minste enheter per salgsenhet",
        "Etterspurt minste salgsenhet","Antall EV-enheter per salgsenhet","EV-enhet",
        "Tilbudt pris pr salgsenhet","Tilbudt pris pr minste enhet","Tilbudt pris per EV-enhet","Totalsum pr. år",
        "Produsent","Produsentens art.nr","Produksjonsland","Link til produktblad",
        "Type Miljømerke","Miljømerke","sertifikatnummer miljømerker"
    ]

    # Battery-specific optional columns (page 14 shows "Antall Wattimer / Antall mAh")
    battery_extra = ["Antall Wattimer", "Antall mAh"]

    if lot1:
        rows.append({
            "sheet": "Lot1_Prisskjema",
            "headers": common_headers,
            "constants": {"lot":"Kontorrekvisita"}
        })
        rc.append({"type":"price_schema","sheet":"Lot1_Prisskjema","source_file":src_file})

    if lot2:
        rows.append({
            "sheet": "Lot2_Prisskjema",
            "headers": common_headers + battery_extra,
            "constants": {"lot":"Batterier","extra_cols":"Antall Wattimer|Antall mAh"}
        })
        rc.append({"type":"price_schema","sheet":"Lot2_Prisskjema","source_file":src_file})

    # Side-tab: Rabatt ved levering til forsyningssenteret (page 21)
    if re.search(r"Rabatt\s+ved\s+levering\s+til\s+forsyningssenteret", t, re.I):
        rows.append({
            "sheet": "Forsyningssenter_rabatt",
            "headers": ["Kunde/forrsyningssenter","Rabatt_pct"],
            "constants": {"customers":["Helse Sør-Øst RHF","Resterende kunder"]}
        })
        rc.append({"type":"price_schema","sheet":"Forsyningssenter_rabatt","source_file":src_file})

    # Side-tab: Påslag ved prising av tilleggssortiment (page 21) – collect group list
    if re.search(r"P[åa]slag\s+ved\s+prising\s+av\s+tilleggsortiment", t, re.I):
        groups = [
            "1 Festemateriell",
            "2 Innbindings- og lamineringsmaskiner og tilbehør",
            "3 Kalender og dagbøker",
            "4 Kontor- og skrivebordstilbehør",
            "5 Konvolutter",
            "6 Kurver og sorteringsutstyr til skrivebord",
            "7 Makuleringsmaskiner og tilbehør",
            "8 Mapper, permer og skilleark",
            "9 Merkemaskin og -tape",
            "10 Oppbevarings- og sorteringsutstyr",
            "11 Papirhullemaskiner og innbindingsmaskiner",
            "12 Papirskjæremaskiner og tilbehør",
            "13 Regnemaskiner og tilbehør",
            "14 Selvklebende etiketter",
            "15 Skriveblokker og notisbøker",
            "16 Skrivemateriell, penner og markører",
            "17 Skriver- og kopipapir",
            "18 Stempler",
            "19 Tavler og tilbehør",
            "20 Tilbehør til kontormaskiner",
            "21 Kontorrekvisita uklassifisert",
            "Batterier og -celler og tilbehør"
        ]
        rows.append({
            "sheet": "Tilleggsortiment_paaslag",
            "headers": ["Varegruppe","Påslag_pct"],
            "constants": {"groups": groups}
        })
        rc.append({"type":"price_schema","sheet":"Tilleggsortiment_paaslag","source_file":src_file})

    return rows, rc


# ---------------- Kravspesifikasjon (Bilag 2) — per-lot M/E krav ----------------
def extract_office_spec(text: str, src_file: str):
    """
    Returns (requirements_rows, receipts)
    Emits:
      - General M-krav (all lots): logistics awareness, packing levels F/L/T, pricing/variant rule, Type-1 ecolabel scoring info (E)
      - Lot 1 Kontorrekvisita: envelope opacity; archive boxes; copy-paper ISO 9706, acid-free/aldringsbestandig, usable in all MFPs, two-sided opacity
      - Lot 2 Batterier: IEC 60086; produced < 12 months; E-criterion for lifetime with docs (mAh, Discharge Curve, Wh)
    """
    t = text
    REQ = []
    RC  = []

    def R(req_id, section, kind, pk, hint, txt, row):
        REQ.append({"req_id":req_id,"section":section,"kind":kind,"prompt_kind":pk,
                    "value_hint":hint,"krav_text":txt,"source_file":src_file,"source_row":row})

    # ---- General (gjelder alle delkontrakter) ----
    if re.search(r"gjøre seg kjent.*logistikkbetingelser", t, re.I):
        R("GEN-LOG-BEKJENT","Generelle krav","mandatory","boolean","les Bilag 7","Tilbyder skal gjøre seg kjent med Bilag 7 Logistikkbetingelser.", "Veiledning/Generelle")
    if re.search(r"lever(e|es).*ubrutt.*F-?pak.*L-?pak.*T-?pak", t, re.I):
        R("GEN-PAK-FLT","Levering/forpakning","mandatory","boolean","F-pak/L-pak/T-pak","Levering skal kunne skje i ubrutt F-, L- og T-pak.", "Krav 2")
    if re.search(r"prises.*prisskjema", t, re.I) and re.search(r"varianter.*samme.*produsent.*produktserie", t, re.I):
        R("GEN-PRIS-VARIANT","Prising/varianter","mandatory","boolean","samme produsent/serie","Pris i henhold til prisskjema; varianter fra samme produsent/serie som hovedprodukt.", "Krav 3")
    if re.search(r"Type\s*1\s*milj", t, re.I):
        R("GEN-E-MILJO","Miljø (eval)","eval","attachment","Type-1 miljømerke i prisskjema","Type-1 miljømerker gir høyest score; oppgi i prisskjema (AC–AE).", "Krav 4")

    # ---- Lot 1: Kontorrekvisita ----
    if re.search(r"Kontorrekvisita", t, re.I):
        if re.search(r"tiln[aæ]rmet lik.*beskrivelsen.*prisskjema", t, re.I):
            R("L1-PROD-TILSV","Lot 1: Produktkvalitet","mandatory","boolean","som prisskjema/ref.produkt",
              "Tilbudte produkter skal være tilnærmet lik beskrivelsen i prisskjema; der referanseprodukt finnes skal kvalitet være tilsvarende.", "Krav 5")
        if re.search(r"konvolutt.*beskytt.*gjennomlesning|ugjennomsikt", t, re.I):
            R("L1-KONVOLUTT-OPAK","Lot 1: Konvolutter","mandatory","boolean","ugjennomsiktige","Konvolutter skal beskytte mot gjennomlesning (ugjennomsiktige).", "Krav 6")
        if re.search(r"arkivboks.*arkivforskrift", t, re.I):
            R("L1-ARKIVBOKS-FORS","Lot 1: Arkivbokser","mandatory","boolean","arkivforskriften","Arkivbokser skal oppfylle krav i arkivforskriften.", "Krav 7")
        if re.search(r"ISO\s*9706", t, re.I):
            R("L1-PAPIR-ISO9706","Lot 1: Skriver- og kopipapir","mandatory","boolean","ISO 9706","Kopipapir skal oppfylle ISO 9706 (eller tilsvarende).", "Krav 8")
        if re.search(r"syrefritt.*aldringsbestandig", t, re.I):
            R("L1-PAPIR-SYREFRI","Lot 1: Skriver- og kopipapir","mandatory","boolean","syrefritt/aldringsbestandig",
              "Kopipapir skal være syrefritt, aldringsbestandig og oppfylle Riksarkivets krav.", "Krav 9")
        if re.search(r"alle typer.*multifunksjonsmaskiner|kopieringsmaskiner|skrivere", t, re.I):
            R("L1-PAPIR-KOMPAT","Lot 1: Skriver- og kopipapir","mandatory","boolean","bruk i alle MFP/skrivere",
              "Papir skal kunne brukes i alle typer MFP/kopimaskiner/stasjonære skrivere.", "Krav 10")
        if re.search(r"to-?sidig.*ugjennomsiktig", t, re.I):
            R("L1-PAPIR-DUO-OPAK","Lot 1: Skriver- og kopipapir","mandatory","boolean","tosidig utskrift",
              "Papir skal være ugjennomsiktig og kunne brukes til to-sidig utskrift.", "Krav 11")

    # ---- Lot 2: Batterier ----
    if re.search(r"Delkontrakt\s*2.*Batterier", t, re.I):
        R("L2-PROD-TILSV","Lot 2: Produktkvalitet","mandatory","boolean","som prisskjema/ref.produkt",
          "Produktene skal samsvare med prisskjema (anbudslinjenavn, minste salgsenhet, referanseprodukt). Avvik kan underkjennes.", "Krav 12")
        if re.search(r"IEC\s*60086", t, re.I):
            R("L2-IEC60086","Lot 2: Standard","mandatory","boolean","IEC 60086","Batterier skal oppfylle krav i IEC 60086.", "Krav 13")
        if re.search(r"produsert.*(12|tolv)\s*m[åa]neder.*f[øo]r levering", t, re.I):
            R("L2-PROD-<12MND","Lot 2: Produksjonstid","mandatory","boolean","< 12 mnd","Batterier må være produsert mindre enn 12 måneder før levering.", "Krav 14")
        # E-kvalitet: Levetid mAh/DC/Wh
        if re.search(r"levetid.*mAh.*(Discharge|utladningskurve).*Wh", t, re.I):
            R("L2-E-LEVETID","Lot 2: Levetid (eval)","eval","attachment","mAh + DC + Wh",
              "Oppgi levetid og legg ved dokumentasjon: mAh, utladningskurve (Discharge Curve) og antall Wh. Merkes med varelinje-referanse.", "Krav 15")

    return REQ, RC


# ---------------- Rammeavtale (Bilag 13) — common rails ----------------
def extract_office_contract(text: str, src_file: str):
    """
    Returns (terms: dict, req_rows: list, receipts: list)
    Captures: period/extension/probation/notice; delivery DDP & lead-times; stats cadence + LD;
              KPI rules; invoicing/payment incl. wrong-invoice fee; delay LD regime; FM 75/15.
    """
    import re
    t = text
    TERMS, REQ, RC = {}, [], []

    def rc(k,v): RC.append({"type":"contract_term","key":k,"value":v,"source_file":src_file})

    # Period / extension / probation / notice
    m = re.search(r"Avtalens varighet[:\s]*([0-9.]{10})\s*[\u2013-]\s*([0-9.]{10})", t, re.I)
    if m:
        TERMS["contract:start_date"]    = f"{m.group(1)[6:10]}-{m.group(1)[3:5]}-{m.group(1)[0:2]}"; rc("contract:start_date", TERMS["contract:start_date"])
        TERMS["contract:end_date_base"] = f"{m.group(2)[6:10]}-{m.group(2)[3:5]}-{m.group(2)[0:2]}"; rc("contract:end_date_base", TERMS["contract:end_date_base"])
    if re.search(r"forlenge.*1\s*år\s*om gangen", t, re.I):   TERMS["contract:extension_step_years"]=1; rc("contract:extension_step_years",1)
    if re.search(r"maksimal\s+samlet\s+avtaleperiode\s+er\s*4\s*år", t, re.I): TERMS["contract:period_max_years"]=4; rc("contract:period_max_years",4)
    if re.search(r"De første\s*6\s*måneder.*prøvetid", t, re.I): TERMS["contract:probation_months"]=6; rc("contract:probation_months",6)
    if re.search(r"prøvetiden.*30\s*dagers\s*varsel", t, re.I):  TERMS["contract:probation_termination_notice_days"]=30; rc("contract:probation_termination_notice_days",30)
    if re.search(r"skriftlig.*6\s*måneder\s*varsel", t, re.I):    TERMS["contract:termination_notice_months"]=6; rc("contract:termination_notice_months",6)

    # Delivery & logistics
    if re.search(r"levering.*DDP.*Incoterms\s*2020", t, re.I):   TERMS["delivery:incoterms"]="DDP_Incoterms2020"; rc("delivery:incoterms","DDP_Incoterms2020")
    if re.search(r"Leveringstid\s*:\s*-\s*3\s*dager.*-\s*5\s*dager", t, re.I):
        TERMS["delivery:lead_time_hso_hv_hmn_days"]=3; rc("delivery:lead_time_hso_hv_hmn_days",3)
        TERMS["delivery:lead_time_hn_days"]=5;       rc("delivery:lead_time_hn_days",5)

    # Statistics cadence + LD
    if re.search(r"20\.04.*05\.08.*20\.10.*20\.01", t, re.I):  TERMS["stats:quarterly_due_dates"]="20.04;05.08;20.10;20.01"; rc("stats:quarterly_due_dates",TERMS["stats:quarterly_due_dates"])
    if re.search(r"Dagmulkten.*1\s*000\s*per\s*virkedag.*statistikk", t, re.I): TERMS["stats:delay_ld_nok_per_working_day"]=1000; rc("stats:delay_ld_nok_per_working_day",1000)
    if re.search(r"leverandor\.sykehusinnkjop\.no", t, re.I): TERMS["stats:portal_url"]="https://leverandor.sykehusinnkjop.no"; rc("stats:portal_url",TERMS["stats:portal_url"])

    # Pricing / KPI indexation
    if re.search(r"Prisene\s+er\s+faste\s+i\s*12\s*måneder", t, re.I): TERMS["price:fixed_first_months"]=12; rc("price:fixed_first_months",12)
    if re.search(r"varsles\s*2\s*måneder", t, re.I):             TERMS["price:kpi_notice_weeks"]=8; rc("price:kpi_notice_weeks",8)
    if re.search(r"Førstegangs.*KPI.*fra\s*februar\s*2025", t, re.I): TERMS["price:kpi_first_fraction_pct"]=100; rc("price:kpi_first_fraction_pct",100)

    # Invoicing / payment
    if re.search(r"Betalingsfrist\s+er\s*30\s*dager", t, re.I): TERMS["payment:days"]=30; rc("payment:days",30)
    if re.search(r"ikke\s+beregnes.*gebyr", t, re.I):            TERMS["invoice:fee_prohibited"]=True; rc("invoice:fee_prohibited",True)
    if re.search(r"gebyr.*NOK\s*500\s*pr\s*faktura", t, re.I):  TERMS["invoice:wrong_invoice_fee_nok"]=500; rc("invoice:wrong_invoice_fee_nok",500)

    # Delay LD regime
    if re.search(r"Dagmulkten\s+skal\s+utgjøre\s*0,?25\s*%", t, re.I): TERMS["delay:ld_rate_pct_per_working_day"]=0.25; rc("delay:ld_rate_pct_per_working_day",0.25)
    if re.search(r"eller\s*kr\s*800", t, re.I):                    TERMS["delay:ld_min_nok_per_day"]=800; rc("delay:ld_min_nok_per_day",800)
    if re.search(r"Dagmulktperioden.*100\s*virkedager", t, re.I):  TERMS["delay:ld_max_working_days"]=100; rc("delay:ld_max_working_days",100)

    # Force majeure 75/15
    if re.search(r"75\s*kalenderdager.*15\s*kalenderdagers\s*varsel", t, re.I):
        TERMS["force_majeure:termination_days"]=75; rc("force_majeure:termination_days",75)
        TERMS["force_majeure:notice_days"]=15;      rc("force_majeure:notice_days",15)

    # Meetings
    if re.search(r"minst\s+ett\s+årlig\s+status-\s*og\s*evalueringsmøte", t, re.I):
        REQ.append({"req_id":"MOTE-STATUS","section":"Kommunikasjon","kind":"mandatory","prompt_kind":"boolean",
                    "value_hint":"årlig","krav_text":"Minst ett årlig status-/evalueringsmøte; ellers møter med 5 virkedagers varsel.",
                    "source_file":src_file,"source_row":"Pkt 4.3.2"})

    return TERMS, REQ, RC

# ---------------- Logistikkbetingelser (Bilag 7) ----------------
def extract_office_logistics(text: str, src_file: str):
    """
    Returns (terms:dict, req_rows:list, receipts:list) from 'Bilag 7 - Logistikkbetingelser'.
    Captures delivery lead-times, pallet/emballering/merking gates, APL/F/L/T,
    ASN/GS1/CE, holdbarhet rules, returns window, precision/complaint targets & fees.
    """
    import re
    t = text
    TERMS, REQ, RC = {}, [], []

    def term(k,v): RC.append({"type":"contract_term","key":k,"value":v,"source_file":src_file}); TERMS[k]=v
    def R(req_id, section, kind, pk, hint, txt, row):
        REQ.append({"req_id":req_id,"section":section,"kind":kind,"prompt_kind":pk,"value_hint":hint,
                    "krav_text":txt,"source_file":src_file,"source_row":row})

    # Lead times (3 days HSØ/HV/HMN; 5 days HN) – Vedlegg 1 pkt. 2 (p.5)
    if re.search(r"maksimalt\s*tre\s*\(3\)\s*virkedager.*Helse\s*S[øo]r-\S+.*Helse\s*Vest.*Helse\s*Midt", t, re.I):
        term("delivery:lead_time_hso_hv_hmn_days", 3)
    if re.search(r"maksimalt\s*Fem\s*\(5\)\s*virkedager.*Helse\s*Nord", t, re.I):
        term("delivery:lead_time_hn_days", 5)

    # Pallet & packaging – Vedlegg 2 pkt.2–3 (p.14–16)
    if re.search(r"EUR-?pall\s*\(?80\s*x\s*120\s*cm\)?", t, re.I):
        term("packaging:pallet_type", "EUR 80x120")
    if re.search(r"maksimal\s*h[øo]yde\s*p[åa]\s*120\s*cm", t, re.I):
        term("packaging:pallet_height_max_cm", 120)
    if re.search(r"ISPM-?15", t, re.I):
        term("packaging:ispm15_required_for_import_pallet", True)
    if re.search(r"transparent\s+gjenvinnbar\s+transportplast", t, re.I):
        term("packaging:transparent_wrap_required", True)
    if re.search(r"samlepall", t, re.I):
        R("LOGI-MIX-PALL-MERK","Pall/leveranse","mandatory","boolean","samlepall merket",
          "Samlepall skal merkes tydelig som samlepall og like artikler samles på samme pall.", "Vedlegg 2 pkt.2")

    # Sterile varer & 3-lags – Vedlegg 2 pkt.3 (p.16)
    if re.search(r"3-?lags.*emballasje", t, re.I):
        term("packaging:sterile_3layer_required", True)
    if re.search(r"SUL-?vare", t, re.I):
        term("packaging:sul_allowed", True); term("packaging:sul_label_required", True)

    # Marking & identifiers – Vedlegg 2 pkt.4–5 (p.16–18)
    if re.search(r"ASN\s+nummer|Advanced\s+Shipping\s+Note", t, re.I):
        term("marking:asn_required", True)
    if re.search(r"GS1-?128|data\s*matrix", t, re.I):
        term("marking:gs1_required", True)
    if re.search(r"CE-merking", t, re.I):
        term("marking:ce_marking_required", True)
    if re.search(r"LOT-nummer|Batch-nummer", t, re.I):
        term("marking:lot_batch_on_label_required", True)
    if re.search(r"Best f[øo]r dato|utl[øo]psdato", t, re.I):
        term("marking:best_before_label_required", True)

    # APL / F-pak / L-pak / T-pak – Vedlegg 1 pkt.4 (p.7)
    if re.search(r"Avdelingspakkelogistikk|APL", t, re.I):
        R("LOGI-APL-PAK","APL/forpakninger","mandatory","boolean","F-pak/L-pak/T-pak",
          "Leveranse skal følge APL-konseptet; egnet minste forpakning for HF/FS; F-pak/L-pak/T-pak i henhold til pakningsveileder.", "Vedlegg 1 pkt.4")

    # Holdbarhet – Vedlegg 2 pkt.6 (p.18)
    if re.search(r"minimum\s*2/3\s*av\s*total\s*holdbarhet", t, re.I):
        term("shelf_life:min_fraction_two_thirds", True)
    if re.search(r"kortere\s*holdbarhet\s*enn\s*12\s*m[åa]neder\s*aksepteres.*unntak", t, re.I):
        term("shelf_life:min_months_rule_with_exceptions", 12)

    # Returns & pickup – Vedlegg 4 pkt.2–3 (p.25–29)
    if re.search(r"hente\s+varer\s+.*\s*senest\s*innen\s*10\s*virkedager", t, re.I):
        term("returns:pickup_within_working_days", 10)
    R("LOGI-RETUR-KRITERIER","Retur/holdbarhet","mandatory","attachment","salgbar/ubrutt F/L-pak",
      "Retur kan kreves i særskilte tilfeller; varer i salgbar stand og i ubrutt original F-/L-pak (sterile varer minst 2-lags).", "Vedlegg 4 pkt.3.4")

    # Precision & complaint targets + fees – Vedlegg 5 (p.30–31)
    if re.search(r"leveringspresisjon.*96\s*%", t, re.I):
        term("logistics:delivery_precision_target_pct", 96)
    if re.search(r"reklamasjonsgrad.*0[,\.]5\s*%", t, re.I):
        term("logistics:complaint_max_pct", 0.5)
    if re.search(r"1\s*000\s*(kr|nok).*reklamasjon", t, re.I):
        term("logistics:complaint_fee_nok", 1000)
    # Delay-fee tiers by unit price (3.5% / 1.0% / 0.5%, cap 40 days)
    if re.search(r"3,?5\s*%.*0,1.*9,?9999.*1,?0\s*%.*10.*499,?9999.*0,?5\s*%.*500", t, re.I|re.S):
        term("logistics:delay_fee_per_day_schema", "3.5% (0.1–9.9999), 1.0% (10–499.9999), 0.5% (>=500)")
    if re.search(r"inntil\s*40\s*virkedager", t, re.I):
        term("logistics:delay_fee_cap_days", 40)

    # Hasteordre same-day – Vedlegg 4 pkt.1 (p.24)
    if re.search(r"Hasteordre.*samme dag", t, re.I):
        term("order:urgent_same_day_response", True)

    return TERMS, REQ, RC


# ---------------- Elektronisk samhandlingsavtale (Helse Nord) ----------------
def extract_office_edi(text: str, src_file: str):
    """
    Returns (terms:dict, req_rows:list, receipts:list) from the regional EDI note.
    Captures: EHF required, provider (Vieri AS), 3-step activation, contact email.
    """
    import re
    t = text
    TERMS, REQ, RC = {}, [], []

    def term(k,v): RC.append({"type":"contract_term","key":k,"value":v,"source_file":src_file}); TERMS[k]=v
    def R(req_id, section, kind, pk, hint, txt, row):
        R = {"req_id":req_id,"section":section,"kind":kind,"prompt_kind":pk,"value_hint":hint,
             "krav_text":txt,"source_file":src_file,"source_row":row}
        return R

    if re.search(r"elektronisk\s+hand(el|ling).*EHF", t, re.I) or re.search(r"EHF-?meldinger", t, re.I):
        term("edi:ehf_required", True)
    if re.search(r"Vieri\s+AS", t, re.I):
        term("edi:provider", "Vieri AS")
    # "tre steg" to be approved on new messages
    if re.search(r"tre\s+steg\s+gjennomf[øo]res", t, re.I):
        term("edi:activation_steps", 3)
    m = re.search(r"[A-Za-z0-9._%+-]+@helse-nord\.no", t, re.I)
    if m:
        term("edi:contact_email", m.group(0))

    # Structure-only requirement: sign EDI agreement before start
    REQ.append({"req_id":"EDI-SIGN","section":"Elektronisk samhandling","kind":"mandatory","prompt_kind":"attachment",
                "value_hint":"signert samhandlingsavtale","krav_text":"Signert elektronisk samhandlingsavtale skal foreligge før oppstart.",
                "source_file":src_file,"source_row":"Intro"})
    # Structure-only: test order/order response/invoice before go-live
    REQ.append({"req_id":"EDI-TEST","section":"Elektronisk samhandling","kind":"mandatory","prompt_kind":"boolean",
                "value_hint":"ordre/ordresvar/faktura testet","krav_text":"EHF-ordre, ordresvar og faktura skal være testet og verifisert før go-live.",
                "source_file":src_file,"source_row":"Prosess"})

    return TERMS, REQ, RC
