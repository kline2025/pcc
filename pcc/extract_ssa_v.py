import re
from typing import List, Dict, Tuple

def _fc(item, value, src, snip):
    return {"item": item, "value": value, "source_file": src, "source_snippet": snip}

# ---------------- ITT (Konkurransebestemmelser – HN IKT SSA-V) ----------------
def extract_ssa_v_itt(text: str, src_file: str) -> Tuple[List[Dict], List[Dict], List[Dict], List[Dict]]:
    """
    Returns:
      forms_constraints_rows, submission_checklist_rows, criteria_rows, receipts
    Grounded in the dynamic ITT for 'Reanskaffelse lisenser – Service Manager (OpenText)'.
    """
    t = text
    fc: List[Dict] = []
    chk: List[Dict] = []
    cf: List[Dict] = []
    rc: List[Dict] = []

    # Envelope
    if re.search(r"\bMercell\b", t, re.I):
        fc.append(_fc("channel","Mercell",src_file,"Kommunikasjon via Mercell"))
    if re.search(r"\båpen anbudskonkurranse\b", t, re.I):
        fc.append(_fc("procedure","Åpen anbudskonkurranse (del I/III); uten forhandling",src_file,"Anskaffelsesprosedyre"))
    if re.search(r"Alternative tilbud aksepteres ikke", t, re.I):
        fc.append(_fc("alt_offers_allowed", False, src_file, "Alternative tilbud aksepteres ikke"))
    if re.search(r"Parallelle tilbud aksepteres ikke", t, re.I):
        fc.append(_fc("parallel_offers_allowed", False, src_file, "Parallelle tilbud aksepteres ikke"))
    if re.search(r"Tilbudet er bindende i\s*4\s*m[åa]neder", t, re.I):
        fc.append(_fc("bid_validity_months", 4, src_file, "Vedståelsesfrist 4 mnd"))
    if re.search(r"ikke\s+inndelt\s+i\s+delkontrakter", t, re.I):
        fc.append(_fc("lots_allowed", False, src_file, "Ikke inndelt i delkontrakter"))
    if re.search(r"SSA-?V\s+Vedlikeholdsavtale\s+med\s+én\s+leverandør", t, re.I):
        fc.append(_fc("contract_type","SSA-V vedlikeholdsavtale, én leverandør", src_file, "Avtaletype"))
    # Avtaleperiode i ITT
    m = re.search(r"Vedlikeholdsavtalen\s+skal\s+gjelde\s+i\s*1\s*år.*1\+1\+1", t, re.I)
    if m:
        fc.append(_fc("contract_period_base_years", 1, src_file, m.group(0)))
        fc.append(_fc("extension_step_years", 1, src_file, "Opsjon 1+1+1"))

    # Submission checklist (3.2)
    chk_items = [
        ("Tilbudsbrev", True),
        ("Kravspesifikasjon", True),
        ("Prisskjema", True),
        ("Bruksanvisning og begrunnelse for sladding", True),
        ("Sladdet versjon", True),
        ("Forpliktelseserklæring", False),
        ("Morselskapsgaranti", False),
        ("3. partsbetingelser", False),
        ("Egenerklæring om russisk involvering", True),
    ]
    for title, mandatory in chk_items:
        if re.search(re.escape(title), t, re.I):
            chk.append({
                "doc_code": title, "title": title, "phase": "Offer",
                "mandatory": mandatory, "source_file": src_file, "snippet": title
            })

    # Tildelingskriterier (6.1/6.x)
    if re.search(r"Pris\s*70\s*%", t, re.I) and re.search(r"Kvalitet\s*30\s*%", t, re.I):
        cf.append({"criterion":"Pris","weight_pct":70,"group":"price","total_pct":100,
                   "price_model":"relative_method_in_mercell","scoring_model":"relative (Mercell) 10p",
                   "model_anchor":"ITT pkt. 6"})
        cf.append({"criterion":"Kvalitet","weight_pct":30,"group":"quality","total_pct":100,
                   "price_model":"","scoring_model":"evalueringskrav i kravskjema",
                   "model_anchor":"ITT pkt. 6"})
    if re.search(r"Milj[øo]\s+vek(t|tes)\s+ikke", t, re.I):
        rc.append({"type":"contract_term","key":"award:environment_weighted","value":False,"source_file":src_file})

    return fc, chk, cf, rc


# ---------------- SSA-V general avtaletekst (2024) ----------------
def extract_ssa_v_contract(text: str, src_file: str) -> Tuple[Dict, List[Dict], List[Dict]]:
    """
    Returns:
      terms (dict), requirements (list), receipts (list)
    Grounded in SSA-V 2024 general avtaletekst: SLA in Bilag 5, DPA Bilag 11,
    monthly reporting, KPI indexation, EHF invoicing, timebot caps, auto-renewal & notices.
    """
    t = text
    TERMS: Dict[str, object] = {}
    REQ: List[Dict] = []
    RC: List[Dict] = []

    def term(k,v,snip=""): TERMS[k]=v; RC.append({"type":"contract_term","key":k,"value":v,"source_file":src_file,"snippet":snip})

    # Contract family
    term("contract:family","SSA-V","SSA-V 2024")

    # SLA & reporting (Bilag 5)
    if re.search(r"Bilag\s*5.*Tjenesteniv[åa].*standardiserte kompensasjoner", t, re.I):
        term("sla:bilag5_required", True, "Bilag 5 – Tjenestenivå")
    if re.search(r"månedlig\s+rapportering|rapportering\s+skal\s+skje\s+m[åa]nedlig", t, re.I):
        term("sla:reporting_monthly", True, "Pkt. 2.5/rapportering")

    # Feilkategorier A/B/C (fallback if Bilag 5 not present)
    if re.search(r"Kritisk feil.*Alvorlig feil.*Mindre alvorlig feil", t, re.I|re.S):
        term("sla:error_categories", "A,B,C", "Pkt. 2.4.5 – feildefinisjoner")

    # Timebot (0.2 % pr time; cap 5 % pr tilfelle / 15 % pr år)
    if re.search(r"timebot.*0[,\.]2\s*%\s*.*5\s*%\s*.*15\s*%", t, re.I|re.S):
        term("sla:timebot_pct_per_hour", 0.2, "Pkt. 9.4.3")
        term("sla:timebot_cap_pct_per_case", 5, "Pkt. 9.4.3")
        term("sla:timebot_cap_pct_per_year", 15, "Pkt. 9.4.3")

    # Invoicing (EHF)
    if re.search(r"elektronisk\s+faktura.*godkjent standardformat", t, re.I):
        term("invoice:ehf_required", True, "Pkt. 6.2")

    # Indexation (KPI yearly; first from sign month)
    if re.search(r"Timepris.*kan endres.*konsumprisindeks", t, re.I):
        term("price:indexation","KPI_yearly", "Pkt. 6.5.1")

    # Privacy (DPA bilag 11 + obligations)
    if re.search(r"Bilag\s*11.*Databehandleravtale", t, re.I):
        term("privacy:dpa_required", True, "Pkt. 7.3 / Bilag 11")
    if re.search(r"overf[øo]res.*utenfor\s+EU/EØS", t, re.I):
        term("privacy:third_country_transfer_control", True, "Pkt. 7.3")
    if re.search(r"underleverand[øo]rer.*skal.*tilsvarende forpliktelser", t, re.I):
        term("privacy:subprocessor_flowdown", True, "Pkt. 7.3")

    # Varighet & renewal/notice (general model; specifics may be set in bilagene)
    if re.search(r"gjelder i\s*3\s*år.*fornyes.*1\s*år", t, re.I):
        term("contract:auto_renewal_allowed", True, "Pkt. 4.1")
        term("contract:auto_renewal_period_years", 1, "Pkt. 4.1")
    if re.search(r"opp(sig|h)else.*3\s+m[åa]neder", t, re.I):
        term("contract:notice_customer_months", 3, "Pkt. 4.1")
    if re.search(r"Leverand[øo]ren.*12\s+m[åa]neder", t, re.I):
        term("contract:notice_supplier_months", 12, "Pkt. 4.1")
    if re.search(r"alene.*vedlikehold.*24\s+m[åa]neder", t, re.I):
        term("contract:notice_supplier_months_if_monopoly", 24, "Pkt. 4.1")

    return TERMS, REQ, RC

# ---------------- Bilag 5 – Tjenestenivå (SLA) ----------------
def extract_ssa_v_sla(text: str, src_file: str):
    """
    SSA-V Bilag 5 (SLA). If the file is a template, we emit structure gates only.
    If concrete numbers exist (uptime %, response/restore), we capture them.
    Returns (terms, req_rows, receipts).
    """
    import re
    TERMS, REQ, RC = {}, [], []
    def term(k,v,snip=""): TERMS[k]=v; RC.append({"type":"contract_term","key":k,"value":v,"source_file":src_file,"snippet":snip})
    def R(i,sec,kind,pk,hint,txt,row): REQ.append({"req_id":i,"section":sec,"kind":kind,"prompt_kind":pk,"value_hint":hint,"krav_text":txt,"source_file":src_file,"source_row":row})
    t = text

    term("sla:bilag5_present", True, "Bilag 5 – Tjenestenivå")

    # Structure gates expected in SSA-V SLA
    if re.search(r"Brukerst[øo]tte", t, re.I):          R("SLA-SUPPORT","SLA","mandatory","attachment","servicenivå","Beskriv brukerstøtte (åpningstider, kanaler, mål).","Bilag 5")
    if re.search(r"(feil|incident).*A.*B.*C", t, re.I|re.S):
        term("sla:error_categories_declared", True, "Feilkategorier"); R("SLA-RESP-REST","SLA","mandatory","value","P1/P2/P3 tider","Oppgi responstid/gjenopprettingstid per feilkategori.","Bilag 5")
    if re.search(r"programrettelser|patch", t, re.I):    R("SLA-PATCH","SLA","mandatory","attachment","rutiner/frister","Oppgi rutiner og frister for programrettelser.","Bilag 5")
    if re.search(r"nye versjoner|oppgraderinger", t, re.I): R("SLA-VERSJON","SLA","mandatory","attachment","tilgjengeliggj[øo]ring","Oppgi prosess for nye versjoner.","Bilag 5")
    if re.search(r"kompensasjoner|timebot", t, re.I):   term("sla:compensation_scheme_declared", True, "Pkt. 9.4.3")

    # Optional concrete numbers (if filled in)
    m = re.search(r"oppetid[^%]{0,40}(\d{2,3}[.,]?\d?)\s*%", t, re.I)
    if m:
        try: term("sla:uptime_target_pct", float(m.group(1).replace(',', '.')))
        except: pass
    for sev in ("1","2","3"):
        mr = re.search(rf"\bP?{sev}\b.*?responstid[^0-9]{0,20}(\d+)\s*(min|timer)", t, re.I|re.S)
        mt = re.search(rf"\bP?{sev}\b.*?(gjenoppretting|retting)[^0-9]{0,20}(\d+)\s*(min|timer)", t, re.I|re.S)
        if mr:
            mins = int(mr.group(1)) * (1 if "min" in mr.group(2).lower() else 60)
            term(f"sla:response_p{sev}_minutes", mins)
        if mt:
            mins = int(mt.group(2)) * (1 if "min" in mt.group(3).lower() else 60)
            term(f"sla:restore_p{sev}_minutes", mins)

    return TERMS, REQ, RC


# ---------------- Standard Databehandleravtale (Helse- og omsorgssektoren 2020) ----------------
def extract_ssa_v_dpa(text: str, src_file: str):
    """
    Deterministic DPA tokens: roles, server location NO, third-country transfer control,
    subprocessor flow-down/list/notice, strong auth, access logging, breach notice, return-then-delete.
    Returns (terms, req_rows, receipts).
    """
    import re
    TERMS, REQ, RC = {}, [], []
    def term(k,v,snip=""): TERMS[k]=v; RC.append({"type":"contract_term","key":k,"value":v,"source_file":src_file,"snippet":snip})
    def R(i,sec,kind,pk,hint,txt,row): REQ.append({"req_id":i,"section":sec,"kind":kind,"prompt_kind":pk,"value_hint":hint,"krav_text":txt,"source_file":src_file,"source_row":row})
    t = text

    term("privacy:dpa_template","Helse- og omsorgssektoren v2020")

    if re.search(r"Dataansvarlig.*Databehandler", t, re.I):         term("privacy:roles_declared", True, "Pkt. 1–3")
    if re.search(r"ikke.*f[øo]res\s+ut\s+av\s+Norge", t, re.I):      term("privacy:server_location_no_required", True, "Pkt. 10")
    if re.search(r"godkjennes.*f[øo]r.*tredjeland|EU/EØS", t, re.I): term("privacy:third_country_transfer_requires_consent", True, "Pkt. 10")
    if re.search(r"underleverand[øo]r.*tilsvarende forpliktelser", t, re.I): term("privacy:subprocessor_flowdown", True, "Pkt. 9")
    if re.search(r"oppdatert liste.*Vedlegg 4", t, re.I):            term("privacy:subprocessor_list_required", True, "Pkt. 9")
    if re.search(r"underrette.*planer.*skifte ut underleverand[øo]r", t, re.I): term("privacy:subprocessor_change_notice_required", True, "Pkt. 9")
    if re.search(r"sterk autentisering", t, re.I):                   term("security:strong_auth_required", True, "Pkt. 8.2")
    if re.search(r"registrere.*all[e]?.*tilgang.*spores.*enkelte bruker", t, re.I): term("security:access_logging_required", True, "Pkt. 8.2")
    if re.search(r"uten ugrunnet opphold.*varsle.*brudd", t, re.I):  term("privacy:breach_notice_without_delay", True, "Pkt. 8.2")
    if re.search(r"tilbakef[øo]ring.*slette.*etter opph[øo]r", t, re.I): term("privacy:return_then_delete_required", True, "Pkt. 13")

    R("DPA-VEDL1","DPA","mandatory","attachment","Vedlegg 1 utfylt","Fyll ut Vedlegg 1 (formål, opplysninger, behandlinger).","Vedlegg 1")
    R("DPA-VEDL2","DPA","mandatory","attachment","Vedlegg 2 (TOMs)","Fyll ut Vedlegg 2 (detaljerte sikkerhetstiltak/TOMs).","Vedlegg 2")
    R("DPA-VEDL4","DPA","mandatory","attachment","Vedlegg 4 underleverandører","Før opp underleverandører i Vedlegg 4; hold listen oppdatert.","Vedlegg 4")
    R("DPA-ENDR","DPA","mandatory","attachment","Vedlegg 5/6 endringer","Før endringer ved avtaleinngåelse i Vedlegg 5 og senere i Vedlegg 6.","Vedlegg 5/6")

    return TERMS, REQ, RC

# ---------------- Bilag 2 – Kravspesifikasjon (structure-only rows) ----------------
def extract_ssa_v_spec(text: str, src_file: str):
    """
    Parse rows like "G1.0 ..." / "V4.3 ..." and classify as M (minstekrav) or EK (eval Kvalitet).
    Returns (requirements_rows, receipts).
    """
    import re
    REQ, RC = [], []
    t = text

    def R(req_id, section, kind, pk, hint, txt, row):
        REQ.append({"req_id":req_id,"section":section,"kind":kind,"prompt_kind":pk,
                    "value_hint":hint,"krav_text":txt,"source_file":src_file,"source_row":row})

    # Generic row harvest: codes like G1.0 / V7.2 followed by description text on the same line.
    for m in re.finditer(r"\b([GV]\d+\.\d?)\s+([^\n]+)", t):
        code = m.group(1)
        line = m.group(2).strip()
        # Classify
        kind  = "eval" if re.search(r"\bEK\b", line, re.I) else "mandatory"
        pk    = "value" if "beskriv" in line.lower() else "boolean"
        hint  = "beskriv" if pk == "value" else "bekreft"
        # Section (crude split by first letter – good enough for structure)
        section = "Generelle krav" if code.startswith("G") else "Vedlikehold/Support"
        # Trim trailing “M …/EK …” labels from description
        desc = re.sub(r"\s*\b(EK|M)\b.*$", "", line).strip()
        # Don’t swallow empty or purely decorative lines
        if len(desc) >= 8:
            R(code, section, kind, pk, hint, desc, f"Rad {code}")

    # A few explicit gates we know exist (from the visible table images/pages)
    # - minimum 2 statusmøter pr år (V5.3) (page 7)
    if re.search(r"V5\.3.*2\s+statusm[øo]ter", t, re.I):
        R("V5.3","Samhandling","mandatory","boolean","2 pr år",
          "Tilbyder skal stille på minimum 2 statusmøter pr år.", "Kravspesifikasjon s.7")
    # - feilretting A/B/C frister (V9.9) – handled as eval prompt
    if re.search(r"V9\.9.*A.*B.*C.*frister", t, re.I):
        R("V9.9","Krav til feilretting","eval","value","frister per A/B/C",
          "Oppgi frister for A-, B- og C-feil (jfr. SSA-V 2.4.5.1).", "Kravspesifikasjon s.8")

    return REQ, RC


# ---------------- Bilag 1 – Prisskjema (license/support + option) ----------------
def extract_ssa_v_price_schema(text: str, src_file: str):
    """
    Build a canonical price-schema for SSA-V Service Manager:
      Sheet 1: maintenance on existing named/concurrent users
      Sheet 2: option/suppleringskjøp + hourly consultancy
    Returns (sheet_rows, receipts)
    """
    rows, rc = [], []

    # visible headers on page 7 (Vedlikehold-tab) and option-tab (same structure but 'suppleringskjøp')
    base_headers = [
        "Linjenr.", "Oppdragsgivers beskrivelse",
        "Ev.supplerende informasjon/kommentar",
        "Antatt mengde pr. år", "Enhet",
        "Tilbyders art.nr", "Tilbyders artikkelnavn",
        "Kort beskrivelse/kommentar til tilbudt produkt",
        "Tilbudt pris pr enhet for vedlikehold", "Totalsum pr. år",
        "Produsent", "Produsentens art.nr", "Produksjonsland",
        "Listepris/veil.pris pr salgsenhet (angi evnt rabatt %)"
    ]

    rows.append({
        "sheet":"SSA_V_Maintenance",
        "headers": base_headers,
        "constants":{"lot":"Service Manager","note":"Vedlikeholdslisenser (named+concurrent)"}  # page 7 block
    })
    rc.append({"type":"price_schema","sheet":"SSA_V_Maintenance","source_file":src_file})

    option_headers = [
        "Linjenr.", "Oppdragsgivers beskrivelse",
        "Ev.supplerende informasjon/kommentar",
        "Antatt mengde pr. år", "Enhet",
        "Tilbyders art.nr", "Tilbyders artikkelnavn",
        "Kort beskrivelse/kommentar til tilbudt produkt",
        "Tilbudt pris pr enhet for suppleringskjøp", "Totalsum",
        "Produsent", "Produsentens art.nr", "Produksjonsland",
        "Listepris/veil.pris pr salgsenhet (angi evnt rabatt %)"
    ]
    rows.append({
        "sheet":"SSA_V_Option_Suppleringskjop",
        "headers": option_headers,
        "constants":{"includes_consultancy_timeprice":True,"note":"opsjon + konsulenttime (eval)"}  # page 7 second table
    })
    rc.append({"type":"price_schema","sheet":"SSA_V_Option_Suppleringskjop","source_file":src_file})

    return rows, rc

# ---------------- Servicetilgangsavtale – Avtalemal ----------------
def extract_ssa_v_service_access(text: str, src_file: str):
    """
    Deterministic rails from HN IKT service-access template.
    Returns (terms, req_rows, receipts).
    """
    import re
    TERMS, REQ, RC = {}, [], []
    def term(k,v,snip=""): TERMS[k]=v; RC.append({"type":"contract_term","key":k,"value":v,"source_file":src_file,"snippet":snip})
    def R(i,sec,kind,pk,hint,txt,row): REQ.append({"req_id":i,"section":sec,"kind":kind,"prompt_kind":pk,"value_hint":hint,"krav_text":txt,"source_file":src_file,"source_row":row})
    t = text

    # Scope vs DPA precedence
    if re.search(r"skal.*benyttes.*ikke.*personopplysninger", t, re.I):
        term("privacy:service_access_only_if_no_personal_data", True, "Formål/Omfang")
    if re.search(r"databehandleravtale.*har forrang", t, re.I):
        term("privacy:dpa_takes_precedence_over_service_access", True, "Formål/Omfang")

    # Remote access via HN IKT solution; personal account; all use logged
    if re.search(r"HN\s*IKT.*fjernaksessl[øo]sning", t, re.I):
        term("remote_access:hnikt_solution_required", True, "Fjernaksess")
    if re.search(r"personlig\s+brukerkonto", t, re.I):
        term("remote_access:personal_account_only", True, "Fjernaksess")
    if re.search(r"all\s+bruk\s+vil\s+bli\s+logget", t, re.I):
        term("remote_access:all_use_logged", True, "Fjernaksess")
    if re.search(r"kun\s+medarbeidere\s+som\s+har\s+tjenstlig\s+behov", t, re.I):
        term("access:least_privilege_required", True, "Fjernaksess")
    if re.search(r"oversikt.*til enhver tid.*benyttet fjernaksess", t, re.I):
        term("access:maintain_authorized_user_list", True, "Fjernaksess")
    if re.search(r"andre\s+l[øo]sninger.*etter avtale.*risikovurdering", t, re.I):
        term("remote_access:alternate_only_by_agreement", True, "Fjernaksess")
        term("remote_access:risk_assessment_required_for_alt", True, "Fjernaksess")
        term("remote_access:supplier_log_monitor_alt_required", True, "Fjernaksess")

    # Incident/avvik handling
    if re.search(r"varsles\s+omg[åa]ende|uten ugrunnet opphold", t, re.I):
        term("security:incident_notice_without_delay", True, "Hendelseshåndtering")
    if re.search(r"avvikets natur.*årsak.*tidspunkt.*konsekvenser.*tiltak", t, re.I):
        term("security:incident_notice_detail_required", True, "Hendelseshåndtering")

    # Training & NDA
    if re.search(r"tilstrekkelig\s+oppl[æe]ring", t, re.I):
        term("training:infosec_required", True, "Opplæring")
    if re.search(r"taushetserkl[æe]ring", t, re.I):
        term("confidentiality:nda_required", True, "Taushetsplikt")

    # Audit right 30 calendar days’ notice
    if re.search(r"revidere.*minimum\s*30\s*kalenderdager", t, re.I):
        term("audit:notice_days", 30, "Revisjon")

    # Subprocessors
    if re.search(r"underleverand[øo]r.*tilsvarende forpliktelser", t, re.I):
        term("subprocessor:flowdown_required", True, "Bruk av underleverandør")
    if re.search(r"angitt i vedlegg", t, re.I):
        term("subprocessor:list_in_appendix_required", True, "Vedlegg 1")
    if re.search(r"underrette.*skifte ut underleverand[øo]r", t, re.I):
        term("subprocessor:change_notice_required", True, "Bruk av underleverandør")
    if re.search(r"utenfor\s+EØS.*forh[åa]ndsgodkjennes", t, re.I):
        term("subprocessor:outside_eea_requires_consent", True, "Bruk av underleverandør")

    # Formalities
    term("communications:written_required", True, "Meddelelser")
    term("contract:duration_until_all_related_end", True, "Varighet og opphør")

    return TERMS, REQ, RC


# ---------------- Kundens tekniske plattform (Bilag 3) ----------------
def extract_ssa_v_platform(text: str, src_file: str):
    """
    Deterministic platform expectations from Bilag 3.
    Returns (terms, req_rows, receipts).
    """
    import re
    TERMS, REQ, RC = {}, [], []
    def term(k,v,snip=""): TERMS[k]=v; RC.append({"type":"contract_term","key":k,"value":v,"source_file":src_file,"snippet":snip})
    def R(i,sec,kind,pk,hint,txt,row): REQ.append({"req_id":i,"section":sec,"kind":kind,"prompt_kind":pk,"value_hint":hint,"krav_text":txt,"source_file":src_file,"source_row":row})
    t = text

    # Network & access
    if re.search(r"NAC.*802\.1x|802\.1x", t, re.I):               term("tech:nac_8021x_required", True, "Nettverk")
    if re.search(r"IPSec.*VPN.*Citrix.*ICA", t, re.I):            term("vpn:ipsec_remote_access_and_citrix_ica", True, "Fjernaksess")
    if re.search(r"PAM\s+Safeguard", t, re.I):                    term("auth:pam_safeguard_required", True, "IOTS/PAM")
    if re.search(r"tofaktor|multifaktor|MFA", t, re.I):           term("auth:mfa_required", True, "Autentisering")
    if re.search(r"Azure\s+AD.*OIDC|OAuth2|SAML", t, re.I):       term("auth:azure_ad_oidc_oauth2_saml_required", True, "Identitet/Autentisering")

    # Server OS & hardening
    if re.search(r"Windows.*Enterprise.*Red Hat Enterprise Linux", t, re.I):
        term("os:server_windows_enterprise_supported", True, "OS")
        term("os:rhel_only_supported", True, "OS")
    if re.search(r"SMBv1.*(ikke|skal\s+ikke)", t, re.I):
        term("os:no_smbv1", True, "OS-protokoller")
    if re.search(r"Ansible|Red Hat Satellite", t, re.I):          term("os:ansible_satellite_required", True, "Patching")
    if re.search(r"MSIX.*2026", t, re.I):                         term("packaging:msix_required_by", "2026-01-01", "Pakking og distribusjon")

    # SKM / Backup / DB / Web
    if re.search(r"VMware Cloud Foundation|VCF", t, re.I):        term("platform:skm_vcf", True, "SKM")
    if re.search(r"Comm[Vv]ault", t, re.I):                       term("backup:commvault_required", True, "Backup/DSDR")
    if re.search(r"\b(MSSQL|Oracle|MySQL)\b", t, re.I):           term("db:engines_supported", "MSSQL,Oracle,MySQL", "Databaser")
    if re.search(r"IIS\s*10.*F5", t, re.I):                       term("web:iis10_plus_f5_required", True, "Web")

    # User data / MDM
    if re.search(r"OneDrive.*SharePoint", t, re.I):               term("user_data:onedrive_sharepoint_preferred", True, "Brukerdata")
    if re.search(r"Workspace\s*One", t, re.I):                    term("mdm:workspace_one_required", True, "MDM")

    # Change enablement / notice
    if re.search(r"varsler\s+senest\s*7\s*dager", t, re.I):
        term("change:notice_days", 7, "Change enablement – ITIL 4")

    # Security operations
    if re.search(r"(Nmap|Nessus)", t, re.I):                      term("security:vuln_scan_tools", "nmap,nessus", "Sårbarhetssjekk")
    if re.search(r"HelseCERT", t, re.I):                          term("security:helsecert_pentest", True, "Penetrasjonstester")

    # Identity & service accounts
    if re.search(r"OIDC/OAuth2|SAML", t, re.I):                   R("IDP-OPEN","Identitet/Aut","mandatory","boolean","OIDC/OAuth2/SAML",
                                                                    "Eksterne apper skal støtte OIDC/OAuth2 eller SAML via Azure AD.", "IOTS")
    if re.search(r"servicekonto.*lavest.*rettigheter", t, re.I):  term("service_accounts:least_privilege_required", True, "Servicekontoer")
    if re.search(r"bytte av passord.*periodisk", t, re.I):        term("service_accounts:password_rotation_required", True, "Servicekontoer")
    if re.search(r"HelseID", t, re.I):                            term("external_comm:helseid_required_for_patient_data", True, "Ekstern kommunikasjon")

    return TERMS, REQ, RC
