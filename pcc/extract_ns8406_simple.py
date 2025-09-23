import re
from typing import List, Dict, Tuple

def _fc(item, value, src, snip):
    return {"item": item, "value": value, "source_file": src, "source_snippet": snip}

def _norm_date(s: str) -> str:
    m = re.search(r"(\d{2})[./-](\d{2})[./-](\d{4})", s)
    if not m:
        return s.strip()
    d, mn, y = m.groups()
    return f"{y}-{mn}-{d}"

# ---------------- ITT (Konkurransegrunnlag Rossevann VV E01) ----------------
def extract_ns8406_itt(text: str, src_file: str) -> Tuple[List[Dict], List[Dict], List[Dict], List[Dict]]:
    """
    Returns:
      forms_constraints_rows, criteria_rows, requirements_rows, receipts
    Grounded in Konkurransegrunnlag Rossevann VV (E01).
    """
    t = text
    fc: List[Dict] = []
    cf: List[Dict] = []
    req: List[Dict] = []
    rc:  List[Dict] = []

    # Envelope / process
    if re.search(r"\bMercell\b", t, re.I):
        fc.append(_fc("channel","Mercell",src_file,"Kommunikasjon via Mercell"))
    if re.search(r"\båpen anbudskonkurranse\b", t, re.I):
        fc.append(_fc("procedure","Åpen anbudskonkurranse",src_file,"Åpen anbudskonkurranse"))
    if re.search(r"Tilbudets vedst[åa]elsesfrist.*3\s*M[åa]neder", t, re.I):
        fc.append(_fc("bid_validity_months",3,src_file,"Vedståelsesfrist 3 mnd"))
    # Del/alt/parallel (all disallowed)
    if re.search(r"ikke\s+adgang\s+til\s+å\s+gi\s+deltilbud", t, re.I):
        fc.append(_fc("lots_allowed",False,src_file,"Deltilbud ikke tillatt"))
    if re.search(r"ikke\s+adgang\s+til\s+å\s+gi\s+alternative", t, re.I):
        fc.append(_fc("alt_offers_allowed",False,src_file,"Alternative tilbud ikke tillatt"))
    if re.search(r"ikke\s+adgang\s+til\s+å\s+gi\s+parallelle", t, re.I):
        fc.append(_fc("parallel_offers_allowed",False,src_file,"Parallelle tilbud ikke tillatt"))

    # Dates from pkt. 2.3
    m = re.search(r"Frist for å stille spørsmål[^0-9]{0,20}(\d{1,2}[./-]\d{1,2}[./-]\d{4})\s*([0-2]?\d:\d{2})", t, re.I)
    if m: fc.append(_fc("question_deadline", f"{_norm_date(m.group(1))} {m.group(2)}", src_file, m.group(0)))
    m = re.search(r"Tilbudsfrist[^0-9]{0,20}(\d{1,2}[./-]\d{1,2}[./-]\d{4})\s*([0-2]?\d:\d{2})", t, re.I)
    if m: fc.append(_fc("offer_deadline", f"{_norm_date(m.group(1))} {m.group(2)}", src_file, m.group(0)))
    m = re.search(r"Avtaleinngåelse.*(Medio\s+\w+)", t, re.I)
    if m: fc.append(_fc("contract_award_planned", m.group(1), src_file, m.group(0)))

    # Award criteria & weights (pkt. 4.1)
    if re.search(r"Pris.*35\s*%", t, re.I):
        cf.append({"criterion":"Pris","weight_pct":35,"group":"price","total_pct":100,
                   "price_model":"proportional","scoring_model":"lowest total = 10; others proportionally",
                   "model_anchor":"Pkt. 4.2"})
    if re.search(r"Kompetanse.*25\s*%", t, re.I):
        cf.append({"criterion":"Kompetanse","weight_pct":25,"group":"quality","total_pct":100,
                   "price_model":"","scoring_model":"best=10; others normalized",
                   "model_anchor":"Pkt. 4.3"})
    if re.search(r"Gjennomføringsplan.*10\s*%", t, re.I):
        cf.append({"criterion":"Gjennomføringsplan","weight_pct":10,"group":"quality","total_pct":100,
                   "price_model":"","scoring_model":"best=10; others normalized",
                   "model_anchor":"Pkt. 4.4"})
    if re.search(r"Milj[øo].*30\s*%", t, re.I):
        cf.append({"criterion":"Miljø","weight_pct":30,"group":"quality","total_pct":100,
                   "price_model":"","scoring_model":"weighted subcriteria (mass handling/plan/competence)",
                   "model_anchor":"Pkt. 4.5"})

    # Price formula (pkt. 4.2): score = 10 * lowest/offer
    if re.search(r"Oppnådd\s*score\s*=\s*10\s*x\s*laveste\s*pris\s*/\s*tilbudt\s*pris", t, re.I):
        rc.append({"type":"contract_term","key":"price:eval_method","value":"proportional_lowest_max10","source_file":src_file})

    # Structure-only requirements from 4.1 / 4.3 / 4.5 (no PII)
    if re.search(r"CV.*Vedlegg\s*12", t, re.I):
        req.append({"req_id":"KOMP-CV","section":"Kompetanse","kind":"mandatory","prompt_kind":"attachment",
                    "value_hint":"CV for tre nøkkelroller (maks 3 sider)","krav_text":"Lever CV for tre navngitte roller (anleggsleder grunnarbeid, BAS betong, dykkerleder); maks 3 sider pr CV.",
                    "source_file":src_file,"source_row":"Pkt. 4.1–4.3"})
    if re.search(r"referanseprosjekter", t, re.I):
        req.append({"req_id":"KOMP-REF","section":"Kompetanse","kind":"mandatory","prompt_kind":"attachment",
                    "value_hint":"3 referanser pr CV","krav_text":"Oppgi tre referanseprosjekter siste 5 år pr. person (struktur – ingen PII i matriser).",
                    "source_file":src_file,"source_row":"Pkt. 4.3"})
    if re.search(r"Vedlegg\s*13.*Massehåndtering", t, re.I):
        req.append({"req_id":"MILJO-MASSE-ARK","section":"Miljø","kind":"mandatory","prompt_kind":"attachment",
                    "value_hint":"utfylt mal","krav_text":"Lever utfylt «Vedlegg 13 – Mal Massehåndtering».",
                    "source_file":src_file,"source_row":"Pkt. 4.5"})
    if re.search(r"Plan for ytre miljø", t, re.I):
        req.append({"req_id":"MILJO-YM-PLAN","section":"Miljø","kind":"mandatory","prompt_kind":"attachment",
                    "value_hint":"YM-plan","krav_text":"Lever plan for ytre miljø.",
                    "source_file":src_file,"source_row":"Pkt. 4.5"})
    if re.search(r"tilbakeholder\s*1\.?0?00\.?000.*oppfyllelse.*miljøtiltak", t, re.I):
        rc.append({"type":"contract_term","key":"env:retention_nok_for_measures","value":1000000,"source_file":src_file})

    return fc, cf, req, rc


# ---------------- Contract (Vedlegg 03 – Standard kontraktsbestemmelser NS 8406) ----------------
def extract_ns8406_contract(text: str, src_file: str) -> Tuple[Dict, List[Dict], List[Dict]]:
    """
    Returns:
      terms (dict), requirements (list), receipts (list)
    Grounded in Vedlegg 03 – Kristiansand kommunes kontraktsbestemmelser for enklere entrepriser (NS 8406:2009).
    """
    t = text
    TERMS: Dict[str, object] = {}
    REQ:   List[Dict] = []
    RC:    List[Dict] = []

    def term(k,v, snip=""): TERMS[k]=v; RC.append({"type":"contract_term","key":k,"value":v,"source_file":src_file,"snippet":snip})

    # Contract family (simplified)
    term("contract:family","NS8406","NS 8406:2009 som kontraktsbestemmelser")

    # 1.1 Sikkerhet – byggherre stiller ikke sikkerhet
    if re.search(r"Byggherren\s+stiller\s+ikke\s+sikkerhet", t, re.I):
        term("security:client_security_provided", False, "Pkt. 1.1")

    # 1.2 Forsikring – attester innen 14 dager (blankett 1+2)
    if re.search(r"Forsikringsattest.*14\s*dag", t, re.I):
        term("insurance:attest_required_within_days", 14, "Pkt. 1.2")

    # 1.3 Bytte av nøkkelpersonell – dagmulkt 10 000/dag, cap 10% / 300 000
    if re.search(r"dagmulkt\s+p[åa]\s*NOK\s*10\.?000.*per\s*dag", t, re.I):
        term("personnel:unauthorized_replacement_ld_nok_per_day", 10000, "Pkt. 1.3")
        term("personnel:unauthorized_replacement_cap_pct", 10, "Pkt. 1.3")
        term("personnel:unauthorized_replacement_cap_nok", 300000, "Pkt. 1.3")

    # 1.4 Endringsadgang – 25% netto tillegg
    if re.search(r"endringer\s+utover\s+25\s*%\s+netto\s+tillegg", t, re.I):
        term("change:net_addition_cap_pct", 25, "Pkt. 1.4")

    # 1.5 Vederlagsjustering rigg/drift – formel A,B,C (uendret byggetid) og A,Y,Z (forlenget)
    if re.search(r"0,5\s*A\s*\(\s*B\s*-\s*1,1\s*C\s*\)\s*/\s*C", t, re.I):
        term("compensation:rigg_drift_formula_unchanged", "0.5*A*(B-1.1*C)/C", "Pkt. 1.5 (uendret byggetid)")
    if re.search(r"0,7\s*A\s*\(\s*Z\s*\)\s*/\s*Y", t, re.I):
        term("compensation:rigg_drift_formula_extended", "0.7*A*(Z)/Y", "Pkt. 1.5 (forlenget byggetid)")

    # 1.6 Testperiode tekniske anlegg – 6 mnd + 500 000 NOK tilbakehold
    if re.search(r"Testperiode.*6\s*m[åa]neder", t, re.I):
        term("test:period_months", 6, "Pkt. 1.6")
    if re.search(r"tilbakeholdt\s+beløp\s+p[åa]\s*kr\s*500\.?000", t, re.I):
        term("test:retention_nok", 500000, "Pkt. 1.6")

    # 1.7 Opplæring – plan 2 mnd før overtakelse
    if re.search(r"oppl[æa]ringsplan.*2\s*m[åa]neder.*f[øo]r\s+overtakelse", t, re.I):
        term("training:plan_due_months_before_handover", 2, "Pkt. 1.7")

    # 2 Miljøbestemmelser – maskinpark, tropisk tre, returordning emballasje
    if re.search(r"maskinpark.*Euro\s*5.*Stage\s*III\s*B", t, re.I):
        term("env:machine_emission_transport", "Euro 5 (egen)/Euro 6 (innleid)", "Pkt. 2.1")
        term("env:machine_emission_nonroad", "Stage IIIB (egen)/Stage IV (innleid)", "Pkt. 2.1")
    if re.search(r"ikke\s+benyttes\s+tropisk\s+t[øo]mmer", t, re.I):
        term("env:tropical_timber_prohibited", True, "Pkt. 2.1 Bruk av regnskogprodukter")
    if re.search(r"medlem\s+i\s+en\s+returordning.*emballasje", t, re.I):
        term("packaging:return_scheme_required", True, "Pkt. 2.2")

    return TERMS, REQ, RC

def extract_ns3420_boq(text: str, src_file: str):
    """
    Normalize an NS 3420 description/mengdeliste into a canonical price-schema sheet.
    We don't parse each line item here; we register a stable header set so downstream
    price processing is predictable. Returns (sheet_rows, receipts).
    """
    headers = [
        "Kapittel","Postnr","NS3420","Beskrivelse","Enhet","Mengde",
        "Tekstkode","Mengdegrunnlag","Kommentar"
    ]
    rows = [{
        "sheet": "NS3420_Beskrivelse",
        "headers": headers,
        "constants": {"source":"NS3420","note":"headers canonicalized"}
    }]
    rc = [{"type":"price_schema","sheet":"NS3420_Beskrivelse","source_file":src_file}]
    return rows, rc

def extract_ns8406_env_sha(text: str, src_file: str):
    """
    Detect high-signal Environment/SHA flags present in the description PDFs.
    Returns (requirements_rows, receipts). Structure-only; no PII.
    """
    import re as _re
    req, rc = [], []
    def R(req_id, section, kind, pk, hint, txt, row):
        req.append({
            "req_id": req_id, "section": section, "kind": kind, "prompt_kind": pk,
            "value_hint": hint, "krav_text": txt, "source_file": src_file, "source_row": row
        })
    t = text

    if _re.search(r"SHA-?plan", t, _re.I):
        R("SHA-PLAN","SHA","mandatory","boolean","SHA-plan følger prosjektet",
          "Arbeider skal utføres i henhold til prosjektets SHA-plan. Tiltak i SHA-plan skal prises/inkluderes i rigg og drift.",
          "Beskrivelse – SHA")

    if _re.search(r"Milj[øo]oppf[øo]lgingsplan|\bMOP\b", t, _re.I):
        R("ENV-MOP","Ytre miljø","mandatory","boolean","MOP gjelder",
          "Arbeider skal utføres i henhold til Miljøoppfølgingsplan (MOP). Tiltak i MOP skal være inkludert i prisene.",
          "Beskrivelse – MOP")

    if _re.search(r"Drikkevannsforskrift", t, _re.I):
        R("WATER-REG","Ytre miljø/VA","mandatory","boolean","Drikkevannsforskriften",
          "Drikkevannsforskriften skal ivaretas under hele anleggsperioden.",
          "Beskrivelse – Drikkevann")

    return req, rc

def extract_ns8406_mop(text: str, src_file: str):
    """
    Miljøoppfølgingsplan (MOP)
    Emits structure-only requirements + objective thresholds as contract terms.
    Returns (terms: dict, req_rows: list, receipts: list)
    """
    import re as _re
    TERMS, REQ, RC = {}, [], []
    def term(k,v): TERMS[k]=v; RC.append({"type":"contract_term","key":k,"value":v,"source_file":src_file})
    def R(req_id, section, kind, pk, hint, txt, row):
        REQ.append({"req_id":req_id,"section":section,"kind":kind,"prompt_kind":pk,
                    "value_hint":hint,"krav_text":txt,"source_file":src_file,"source_row":row})
    t = text

    # Binding MOP + meta (date/revision)
    term("env:mop_present", True)
    m = _re.search(r"DATO\s*/\s*REVISJON\s*:\s*([0-9./-]+)\s*/\s*([0-9]{2})", t, _re.I)
    if m:
        # Normalize 13.06.2025 / 00 -> 2025-06-13 + "00"
        d = m.group(1)
        dm = _re.search(r"(\d{2})[./-](\d{2})[./-](\d{4})", d)
        if dm:
            term("env:mop_date", f"{dm.group(3)}-{dm.group(2)}-{dm.group(1)}")
        term("env:mop_revision", m.group(2))

    # Plans required 2 weeks before start (plan for ytre miljø, avfallsplan, beredskapsplan, kontrollplan)
    R("ENV-PLANS-BEFORE-START","Ytre miljø","mandatory","attachment","2 uker før oppstart",
      "Entreprenør skal levere: plan for ytre miljø, avfallsplan, beredskapsplan og kontrollplan for ytre miljø senest 2 uker før oppstart.",
      "MOP – kap. 6 / tabell")

    # Noise blackout for støyende arbeider (1 Feb – 1 Jul)
    if _re.search(r"1\.\s*februar\s*-\s*1\.\s*juli", t, _re.I):
        term("env:noise_restriction_window","01-02..01-07")
        R("ENV-NOISE-BLACKOUT","Støy","mandatory","boolean","1.2–1.7",
          "Støyende arbeider (sprengning på land, peling/pigging, slagboring, utfylling) skal ikke utføres 1.2–1.7 med mindre Statsforvalter fastsetter annet.",
          "MOP – støy/vilt")

    # Siltgardin/oljelenser + rensecontainer med pH-justering
    if _re.search(r"siltgardin", t, _re.I):
        term("env:silt_curtain_required", True)
        R("ENV-SILT-DAILY-CHECK","Vannmiljø","mandatory","boolean","daglig visuell sjekk",
          "Siltgardin og oljelenser skal være installert før oppstart; daglig visuell kontroll og utskifting ved behov.",
          "MOP – vannmiljø")
    if _re.search(r"rensecontainer", t, _re.I):
        term("env:treatment_container_required", True)
        R("ENV-PH-CONTROL","Vannmiljø","mandatory","boolean","pH-justering",
          "Anleggsvann skal renses og pH-justeres i rensecontainer før utslipp.",
          "MOP – vannmiljø")

    # Vibrasjonsmåling iht. NS8141
    if _re.search(r"NS8141", t, _re.I):
        R("ENV-VIB-NS8141","Vibrasjoner","mandatory","boolean","NS8141-krav",
          "Vibrasjoner skal måles/kontrolleres og grenseverdier iht. NS8141 skal overholdes.",
          "MOP – vibrasjoner")

    # 70% sorteringsgrad + månedlig rapportering
    if _re.search(r"70\s*%\s*sorteringsgrad", t, _re.I):
        term("env:waste_sorting_target_pct", 70)
        R("ENV-WASTE-REPORT","Avfall","mandatory","boolean","månedlig rapportering",
          "Avfallsmengder skal rapporteres månedlig; min. 70 % sorteringsgrad.",
          "MOP – avfall")

    return TERMS, REQ, RC


def extract_ns8406_overvaking(text: str, src_file: str):
    """
    Overvåkningsplan – operational thresholds and cadence
    Returns (terms: dict, req_rows: list, receipts: list)
    """
    import re as _re
    TERMS, REQ, RC = {}, [], []
    def term(k,v): TERMS[k]=v; RC.append({"type":"contract_term","key":k,"value":v,"source_file":src_file})
    def R(req_id, section, kind, pk, hint, txt, row):
        REQ.append({"req_id":req_id,"section":section,"kind":kind,"prompt_kind":pk,
                    "value_hint":hint,"krav_text":txt,"source_file":src_file,"source_row":row})
    t = text

    # Measurement parameters and cadence
    if _re.search(r"turbiditet.*pH.*konduktivitet", t, _re.I|_re.S):
        term("env:monitoring:parameters","turbiditet,pH,konduktivitet")
    if _re.search(r"hvert\s*10\s*min", t, _re.I):
        term("env:monitoring:interval_minutes", 10)
    if _re.search(r"SMS", t, _re.I):
        term("env:monitoring:alarm_sms", True)
    if _re.search(r"m[åa]nedlige\s+stikkpr[øo]ver", t, _re.I):
        term("env:monitoring:monthly_samples", True)

    # Thresholds: SS 100 mg/L, pH 6–8.5, turbidity alarm 15 NTU over 20 min
    if _re.search(r"100\s*mg/?l\s*suspendert", t, _re.I):
        term("env:monitoring:ss_max_mg_l", 100)
    pm = _re.search(r"pH\s*(\d[.,]?\d?)\s*[-–]\s*(\d[.,]?\d?)", t, _re.I)
    if pm:
        try:
            lo = float(pm.group(1).replace(',','.')); hi = float(pm.group(2).replace(',','.'))
            term("env:monitoring:ph_min", lo); term("env:monitoring:ph_max", hi)
        except: pass
    if _re.search(r"grenseverdi\s*15\s*NTU.*20\s*min", t, _re.I|_re.S):
        term("env:monitoring:turbidity_alarm_ntu", 15)

    # Structure-only: stop work + inspect siltgardin/renseanlegg on alarm
    R("ENV-ALARM-ACTION","Overvåking","mandatory","boolean","stans arbeid + inspeksjon",
      "Alarm ved brudd på grenseverdi: stans relevante arbeider; umiddelbar visuell kontroll av siltgardin/renseanlegg; utbedre før oppstart.",
      "Overvåkningsplan – tiltak ved brudd")

    return TERMS, REQ, RC
