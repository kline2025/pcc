import re
from typing import List, Dict, Tuple

def _fc(item, value, src, snip):
    return {"item":item,"value":value,"source_file":src,"source_snippet":snip}

def _norm_date(s: str) -> str:
    s=s.strip().replace('.', '-').replace('/', '-')
    m=re.search(r'(\d{1,2})-(\d{1,2})-(\d{2,4})', s)
    if m:
        d,mn,y=m.groups()
        if len(y)==2: y='20'+y
        return f"{y.zfill(4)}-{mn.zfill(2)}-{d.zfill(2)}"
    return s

# ---------------- ITT / Konkurransebestemmelser ----------------
def extract_renhold_itt(text: str, src_file: str) -> Tuple[List[Dict], List[Dict], List[Dict], List[Dict]]:
    """
    Emits:
      - forms_and_constraints rows (Mercell, nb-NO, alt/parallel=NEI, vedståelsesfrist=6m, lots=4, timeline)
      - submission_checklist rows (Tilbudsbrev, Svarskjema erfaring, Bilag 1..8, Prisskjema Excel, Sladdet versjon)
      - criteria_and_formula rows (Pris 50; Kvalitet 50; linear price model)
      - receipts (proof anchors)
    """
    fc=[]; checklist=[]; cf=[]; rc=[]
    t=text

    # Channel / language / comms / procedure
    if re.search(r'\bmercell', t, re.I):
        fc.append(_fc("channel","Mercell",src_file,"Kommunikasjon via Mercell"))
    if re.search(r'\båpen anbudskonkurranse\b', t, re.I):
        fc.append(_fc("procedure","Åpen anbudskonkurranse (del I og III); uten forhandling",src_file,"Åpen anbudskonkurranse"))
    if re.search(r'\bikke (adgang|anledning) til å forhandle\b', t, re.I):
        fc.append(_fc("negotiation_allowed",False,src_file,"Ikke anledning til å forhandle"))
    if re.search(r'språk[:\s]*norsk|skrevet på norsk', t, re.I):
        fc.append(_fc("language","nb-NO",src_file,"Tilbudet skal være skrevet på norsk"))
    if re.search(r'alternative tilbud.*ikke', t, re.I):
        fc.append(_fc("alt_offers_allowed",False,src_file,"Alternative tilbud aksepteres ikke"))
    if re.search(r'parallelle tilbud.*ikke', t, re.I):
        fc.append(_fc("parallel_offers_allowed",False,src_file,"Parallelle tilbud aksepteres ikke"))
    m=re.search(r'vedståelsesfrist[^0-9]{0,20}(\d{1,2})\s*måneder', t, re.I)
    if m:
        fc.append(_fc("bid_validity_months", int(m.group(1)), src_file, m.group(0)))

    # Lots / delkontrakter (4 sykehus)
    if re.search(r'delkontrakt(er)?[^0-9]{0,40}(4|\bfire\b)', t, re.I):
        fc.append(_fc("lots_count",4,src_file,"4 deltilbud (ett pr sykehus)"))

    # Timeline (questions, answers, offer deadline, award, start)
    m=re.search(r'Frist for å stille spørsmål[^0-9]{0,20}(\d{2}\.\d{2}\.\d{4})', t, re.I)
    if m: fc.append(_fc("question_deadline", _norm_date(m.group(1)), src_file, m.group(0)))
    m=re.search(r'frist for å svare[^0-9]{0,20}(\d{2}\.\d{2}\.\d{4})', t, re.I)
    if m: fc.append(_fc("answers_deadline", _norm_date(m.group(1)), src_file, m.group(0)))
    m=re.search(r'Frist for å levere tilbud[^0-9]{0,20}([A-Za-z]*\s*\d{2}\.\d{2}\.\d{4})\s*kl\.*\s*([0-2]?\d[:.]\d{2})', t, re.I)
    if m:
        d=_norm_date(re.search(r'\d{2}\.\d{2}\.\d{4}', m.group(1)).group(0))
        tm=m.group(2).replace('.',':')
        fc.append(_fc("offer_deadline", f"{d} {tm}", src_file, m.group(0)))
    m=re.search(r'Tildelingsbeslutning[^0-9]{0,20}(\d{2}\.\d{2}\.\d{4})', t, re.I)
    if m: fc.append(_fc("award_notice_planned", _norm_date(m.group(1)), src_file, m.group(0)))
    m=re.search(r'Oppstart av avtale[^0-9]{0,20}(\d{2}\.\d{2}\.\d{4})', t, re.I)
    if m: fc.append(_fc("contract_start", _norm_date(m.group(1)), src_file, m.group(0)))

    # Contract type / period
    if re.search(r'rammeavtale', t, re.I):
        fc.append(_fc("contract_type","Rammeavtale (en leverandør pr sykehus)",src_file,"Avtaletype"))
    m=re.search(r'Rammeavtalene gjelder i\s*2\s*år.*01\.06\.2025.*31\.05\.2027', t, re.I)
    if m:
        fc.append(_fc("contract_period_base_years",2,src_file,"01.06.2025–31.05.2027"))
        fc.append(_fc("contract_period_max_years",4,src_file,"Maks samlet 4 år; forlengelse 1 år av gangen"))

    # Checklist (exact list from ITT)
    docs = [
        ("Vedlegg 1","Tilbudsbrev"),
        ("Vedlegg 2","Svarskjema erfaring"),
        ("Bilag 1","Kravspesifikasjon (PDF + Excel)"),
        ("Bilag 2","Prisskjema (PDF)"),
        ("Bilag 5","Egenerklæring om russisk involvering"),
        ("Vedlegg 3","Morselskapsgaranti (ev.)"),
        ("Vedlegg 4","Forpliktelseserklæring (ev.)"),
        ("Vedlegg 5","Bruksanvisning og begrunnelse for sladding"),
        ("Vedlegg 6","Prisskjema (Excel)"),
        ("Vedlegg","Sladdet versjon av tilbudet")
    ]
    for code,title in docs:
        if re.search(re.escape(code), t, re.I):
            checklist.append({"doc_code":code, "title":title, "phase":"Offer", "mandatory": True, "source_file": src_file, "snippet": f"{code} {title}"})

    # Criteria & price model (Pris 50 / Kvalitet 50; linear)
    if re.search(r'Tildelingskriterium.*Pris\s*50\s*%.*Kvalitet\s*50\s*%', t, re.I|re.S):
        cf.append({"criterion":"Pris","weight_pct":50,"group":"price","total_pct":100,
                   "price_model":"linear","scoring_model":"lowest=10; ≥2x lowest → 0","model_anchor":"Vedlegg 6 – prisskjema"})
        cf.append({"criterion":"Kvalitet","weight_pct":50,"group":"quality","total_pct":100,
                   "price_model":"","scoring_model":"0–10 relativ modell","model_anchor":"Kravspesifikasjon"})
        rc.append({"type":"award_weights_total","total_pct":100,"source_file":src_file})
    return fc, checklist, cf, rc

# ---------------- Bilag 1 – Kravspesifikasjon (M/E rows + SLA) ----------------
def extract_renhold_spec(text: str, src_file: str) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """
    Emits:
      - requirements_matrix rows (minstekrav & evalueringskrav)
      - service_sla rows (normal/acute response; quality standard)
      - receipts
    """
    req=[]; sla=[]; rc=[]
    t=text

    def R(req_id, section, kind, pk, hint, txt, row):
        req.append({"req_id":req_id,"section":section,"kind":kind,"prompt_kind":pk,"value_hint":hint,
                    "krav_text":txt,"source_file":src_file,"source_row":row})

    # ---- Generelle minstekrav (p.9 image) ----
    if re.search(r'Språk.*norsk', t, re.I):
        R("M-SPRAK_NO","Generelle krav","mandatory","boolean","norsk","Språk: utførende personell skal kunne snakke, lese og skrive norsk; forstå SDS/prosedyrer på NO/EN.", "p.9")
    if re.search(r'Taushetserklæring', t, re.I):
        R("M-TAUSHET","Generelle krav","mandatory","boolean","","Taushetserklæring må signeres før oppstart; leverandør ansvarlig.", "p.9")
    if re.search(r'ikke.*flere enn to ledd', t, re.I):
        R("M-LEVERANDORLEDD_MAX2","Generelle krav","mandatory","boolean","maks 2 ledd","Maks to ledd i leverandørkjeden; brudd kan gi heving.", "p.9")
    if re.search(r'allmenngjøring|allmenngjort tariff', t, re.I):
        R("M-ALLMENNGJORING","Generelle krav","mandatory","boolean","","Allmenngjort tariff; påseplikt; tilbakehold 2× innsparingen ved brudd.", "p.9")
    if re.search(r'bedriftshelsetjeneste|vernetjeneste|skriftlige arbeidsavtaler', t, re.I):
        R("M-BHT-VERNE-AVTALER","Generelle krav","mandatory","boolean","","BHT, verneombud og skriftlige arbeidsavtaler skal være på plass.", "p.9")

    # ---- Kontakt og oppfølging (p.10) ----
    if re.search(r'fast kontaktperson', t, re.I):
        R("E-FAST_KONTAKTPERSON","Kontakt/oppfølging","eval","description","tilgjengelighet + CV","Fast kontaktperson(er) pr sykehus; beskriv tilgjengelighet; CV vedlegges.", "p.10")
    if re.search(r'kvartalsvis statusmøte', t, re.I):
        R("M-STATUSMOTER_Q","Kontakt/oppfølging","mandatory","boolean","kvartalsvis","Kvartalsvise statusmøter per lokasjon initieres av leverandørens kontakt.", "p.10")
    if re.search(r'Avtaleansvarlig.*INSTA.*(3|III)', t, re.I):
        R("E-AVTALEANSVARLIG_INSTA800_L3","Kontakt/oppfølging","eval","attachment","INSTA-800 nivå ≥3 + fagbrev","Avtaleansvarlig nivå ≥3 (INSTA-800) og fagbrev/tilsv. kompetanse. CV vedlegges.", "p.10")

    # ---- Opplæring (p.10) ----
    if re.search(r'grunnkurs renhold.*grunnkurs.*INSTA\s*800', t, re.I):
        R("M-KOMPETANSE_GRUNNKURS","Opplæring","mandatory","boolean","grunnkurs + INSTA 800 nivå 2",
          "Renholdere: grunnkurs renhold + grunnkurs NS-INSTA 800 (nivå 2).", "p.10")
    if re.search(r'opplæring.*maks 10 personer.*2[-–]4 timer', t, re.I):
        R("M-TEORETISK_OPPLAERING","Opplæring","mandatory","boolean","teoretisk 2–4 t; ikke fakturerbar",
          "Oppdragsgiver gir teoretisk opplæring (inntil 10 ledere, 2–4 t); ikke fakturerbar; leverandør trener eget personell.", "p.10")
    if re.search(r'Praktisk opplæring.*Clean Pilot', t, re.I):
        R("M-PRAKTISK_OPPLAERING","Opplæring","mandatory","boolean","lokal + Clean Pilot",
          "Praktisk opplæring sammen med sykehusets renholdere; Clean Pilot; ny opplæring ved utskifting.", "p.10")

    # ---- Kvalitet og utførelse (p.11) ----
    if re.search(r'kvalitetskontroll.*INSTA\s*800', t, re.I):
        R("M-KVALITET_INSTA800","Kvalitet/utførelse","mandatory","boolean","NS-INSTA 800:2010",
          "Kvalitetskontroll og bedømmelse etter NS-INSTA 800:2010.", "p.11")
    if re.search(r'behandle.*utstyr.*lokaler.*respekt', t, re.I):
        R("M-UTFORING_RESPEKT","Kvalitet/utførelse","mandatory","boolean","","Behandle utstyr og lokaler med respekt etter gjeldende prosedyrer.", "p.11")
    if re.search(r'serviceinnstilt', t, re.I):
        R("M-SERVICEHOLDNING","Kvalitet/utførelse","mandatory","boolean","","Serviceinnstilt opptreden jf. INSTA-800.", "p.11")

    # ---- Tilgang / helse / bekledning (p.11–12) ----
    if re.search(r'Nøkler', t, re.I):
        R("M-NOKLER","Tilgang","mandatory","boolean","","Nøkkelhåndtering inkl. retur ved opphør; fast kontaktperson ansvarlig.", "p.11")
    if re.search(r'symptomfri.*48\s*timer', t, re.I):
        R("M-SYKDOM_48T","Helse","mandatory","boolean","48t symptomfri","Ikke arbeide ved symptomer; 48 timer symptomfri før oppstart.", "p.11")
    if re.search(r'varsle oppdragsgiver ved sykdom', t, re.I):
        R("M-SYK_VARSLE_ERSTATTE","Helse","mandatory","boolean","","Varsle ved sykdom og erstatte bestilt renholder.", "p.11")
    if re.search(r'arbeidstøy.*verneutstyr', t, re.I):
        R("M-ARBEIDSTOY","Bekledning","mandatory","boolean","","Arbeidstøy/verneutstyr etter område; daglig skift; smitte-PPE ved behov.", "p.11–12")
    if re.search(r'MRSA.*TBC|TBC.*MRSA', t, re.I):
        R("M-MRSA_TBC","Helse","mandatory","boolean","","MRSA/TBC-klarering iht. sykehusets prosedyre før oppstart.", "p.11")
    if re.search(r'HMS[-\s]?kort', t, re.I):
        R("M-HMSKORT","Tilgang","mandatory","boolean","","HMS-kort bæres synlig; uten HMS-kort kan vises bort.", "p.12")
    if re.search(r'utstyr.*materiell.*oppdragsgiver.*ansvarlig', t, re.I):
        R("M-UTSTYR_MATERIELL","Utstyr/materiell","mandatory","boolean","","Oppdragsgiver skaffer og bekoster utstyr/materiell; garderobeskap stilles til rådighet.", "p.12")

    # ---- SLA keys (p.12) ----
    m=re.search(r'Normal\s+responstid[^0-9]{0,20}(\d{1,3})\s*timer', t, re.I)
    if m:
        sla.append({"key":"sla.normal_response_hours","value":int(m.group(1)),"unit":"hours","text":"Normal responstid"})
        rc.append({"type":"service_sla","key":"sla.normal_response_hours","value":int(m.group(1)),"unit":"hours","source_file":src_file})
    m=re.search(r'responstid.*akuttsituasjon[^0-9]{0,20}(\d{1,3})\s*timer', t, re.I)
    if m:
        sla.append({"key":"sla.acute_response_hours","value":int(m.group(1)),"unit":"hours","text":"Responstid ved akuttsituasjon"})
        rc.append({"type":"service_sla","key":"sla.acute_response_hours","value":int(m.group(1)),"unit":"hours","source_file":src_file})
    if re.search(r'INSTA\s*800', t, re.I):
        sla.append({"key":"quality.standard","value":"NS-INSTA 800","unit":"","text":"Kvalitetsstandard"})
        rc.append({"type":"service_quality","key":"quality.standard","value":"NS-INSTA 800","source_file":src_file})

    # Evalueringskrav (bemanning/responstid, kvalitetssystem)
    if re.search(r'Beskriv antall renholdspersonell.*responstid', t, re.I):
        R("E-BEMANNING_RESPONSTID","Responstid og ressurser","eval","description","antall + responstid",
          "Beskriv antall renholdere pr lokasjon/dag (normalt/akutt) og responstid; vektes positivt.", "p.12")
    if re.search(r'kvalitetssystem.*rutiner', t, re.I):
        R("E-KVALITETSRUTINER","Kvalitetssystem","eval","attachment","system + rutiner",
          "Redegjør for kvalitetssystem og rutiner (oppstart, responstid/hast, fravær, opplæring INSTA-800 og Svanemerket, fagbrev/språkkurs, HSE-hendelser).", "p.12")

    return req, sla, rc


# ---------------- Prisskjema (.xlsx/.pdf) + Bilag 2 (invoicing) ----------------
def extract_renhold_price_forms(text_excel: str, src_excel: str, text_docx: str, src_docx: str):
    """Return (price_rows, contract_terms, receipts).
       price_rows -> rows for write_price_schema_csv
       contract_terms -> dict for write_contract_terms_csv (EHF/PEPPOL etc.)
    """
    price_rows = []
    terms = {}
    rc = []

    # ---- Price schema from Vedlegg 6 (PDF) ----
    if text_excel:
        # Overall share weights (page 1 header table): 80% daily + 20% hovedrenhold
        price_rows.append({
            "sheet": "Prisskjema_Oversikt",
            "headers": "Kategori|Andel",
            "constants": str({"share_daily_pct": 80, "share_hoved_pct": 20})
        })
        rc.append({"type":"price_note","key":"share_daily_pct","value":80,"source_file":src_excel})
        rc.append({"type":"price_note","key":"share_hoved_pct","value":20,"source_file":src_excel})

        # Daily cleaning slot weights (page 1 grid)
        daily_weights = {
            "Hverdager 06:00–21:00": 60.0,
            "Hverdager 21:00–06:00": 30.0,
            "Lørdag 06:00–18:00": 1.0,
            "Lørdag 18:00–21:00": 1.0,
            "Lørdag 21:00–00:00": 1.0,
            "Søndag 00:00–06:00": 2.0,
            "Søndag 06:00–21:00": 2.0,
            "Søndag 21:00–06:00": 1.0,
            "Helligdag 06:00–21:00": 1.0,
            "Helligdag 21:00–06:00": 1.0
        }
        price_rows.append({
            "sheet": "Prisskjema_DagligRenhold",
            "headers": "Tidspunkt|Timepris_ex_mva|Vekting_pct",
            "constants": str({"weights": daily_weights})
        })
        rc.append({"type":"price_schema","sheet":"Prisskjema_DagligRenhold","source_file":src_excel})

        # Hovedrenhold weights (page 2 list – order as presented)
        hoved_weights = [50.0, 30.0, 5.0, 5.0, 2.5, 2.5, 2.5, 2.5]
        price_rows.append({
            "sheet": "Prisskjema_Hovedrenhold",
            "headers": "Slot|Timepris_ex_mva|Vekting_pct",
            "constants": str({"weights_ordered": hoved_weights})
        })
        rc.append({"type":"price_schema","sheet":"Prisskjema_Hovedrenhold","source_file":src_excel})

    # ---- Invoicing/marking from Bilag 2 (DOCX) ----
    if text_docx:
        # EHF/ELMA/PEPPOL and marking requirements
        if "E-faktura" in text_docx or "EHF" in text_docx:
            terms["invoice:electronic_required"] = True
            rc.append({"type":"contract_term","key":"invoice:electronic_required","value":True,"source_file":src_docx})

        # ELMA e-ID (org.nr for ELMA)
        import re
        m = re.search(r"e-?ID[:\s]*([0-9\s]{9})", text_docx, re.I)
        if m:
            eid = m.group(1).replace(" ", "")
            terms["invoice:elma_eid"] = eid
            rc.append({"type":"contract_term","key":"invoice:elma_eid","value":eid,"source_file":src_docx})

        # PEPPOL prefix for foreign suppliers
        if "prefix 9908" in text_docx:
            terms["invoice:peppol_prefix"] = "9908"
            rc.append({"type":"contract_term","key":"invoice:peppol_prefix","value":"9908","source_file":src_docx})

        # Invoice support email
        m = re.search(r"faktura@[^\s]+", text_docx, re.I)
        if m:
            terms["invoice:email"] = m.group(0)
            rc.append({"type":"contract_term","key":"invoice:email","value":m.group(0),"source_file":src_docx})

        # Attachment formats (PDF/TIFF) and unique names
        if "PDF" in text_docx or "TIFF" in text_docx:
            terms["invoice:attachment_formats"] = "PDF,TIFF"
            rc.append({"type":"contract_term","key":"invoice:attachment_formats","value":"PDF,TIFF","source_file":src_docx})
        if "unike navn" in text_docx or "unikt navn" in text_docx:
            terms["invoice:attachment_unique_names"] = True
            rc.append({"type":"contract_term","key":"invoice:attachment_unique_names","value":True,"source_file":src_docx})

        # Reference marking (bestillings-/ansvarsnummer)
        if "Bestillingsnummer" in text_docx or "Innkjøpsnummer" in text_docx:
            terms["invoice:reference_required"] = "Innkjøpsnr (9 siffer) eller Ansvarsnr (6 siffer) + bestillers navn"
            rc.append({"type":"contract_term","key":"invoice:reference_required","value":terms["invoice:reference_required"],"source_file":src_docx})

    return price_rows, terms, rc

# ---------------- Rammeavtale: contract terms ----------------
def _norm_date_ddmmyyyy(s: str) -> str:
    import re
    m = re.search(r"(\d{2})[./-](\d{2})[./-](\d{4})", s)
    if not m:
        return s.strip()
    d, mn, y = m.groups()
    return f"{y}-{mn}-{d}"

def extract_renhold_contract(text: str, src_file: str):
    """Return (terms:dict, req_rows:list, receipts:list) from the framework agreement."""
    import re
    t = text
    TERMS: dict = {}
    REQ:   list = []
    RC:    list = []

    def rc_term(k,v):
        RC.append({"type":"contract_term","key":k,"value":v,"source_file":src_file})

    # Period / extension / probation
    m = re.search(r"Avtalens varighet[:\s]*([0-9.]{10})[-–]([0-9.]{10})", t, re.I)
    if m:
        TERMS["contract:start_date"]    = _norm_date_ddmmyyyy(m.group(1))
        TERMS["contract:end_date_base"] = _norm_date_ddmmyyyy(m.group(2))
        rc_term("contract:start_date", TERMS["contract:start_date"])
        rc_term("contract:end_date_base", TERMS["contract:end_date_base"])
    if re.search(r"Maksimal samlet avtaleperiode\s*er\s*4\s*år", t, re.I):
        TERMS["contract:period_max_years"] = 4; rc_term("contract:period_max_years",4)
    if re.search(r"forlenge.*1\s*år\s*om gangen", t, re.I):
        TERMS["contract:extension_step_years"] = 1; rc_term("contract:extension_step_years",1)
    if re.search(r"De første\s*6\s*måneder.*prøvetid", t, re.I):
        TERMS["contract:probation_months"] = 6; rc_term("contract:probation_months",6)
    if re.search(r"prøvetiden.*30\s*dagers\s*varsel", t, re.I):
        TERMS["contract:probation_termination_notice_days"] = 30; rc_term("contract:probation_termination_notice_days",30)
    if re.search(r"oppsigelse.*9\s*måneder", t, re.I):
        TERMS["contract:termination_notice_months"] = 9; rc_term("contract:termination_notice_months",9)

    # Transfer / assignment
    if re.search(r"Oppdragsgiver kan overdra", t, re.I):
        TERMS["assignment:buyer_transfer_allowed"] = True; rc_term("assignment:buyer_transfer_allowed",True)
    if re.search(r"Leverandøren kan bare overdra.*skriftlig samtykke", t, re.I):
        TERMS["assignment:supplier_transfer_requires_consent"] = True; rc_term("assignment:supplier_transfer_requires_consent",True)

    # Ordering / cancellation
    if re.search(r"Bestilling\s+skal.*inneholde.*Bestillingsnummer", t, re.I):
        REQ.append({"req_id":"ORD-BEST","section":"Bestilling","kind":"mandatory","prompt_kind":"attachment",
                    "value_hint":"bestillingsnr/kundenr/leveringssted",
                    "krav_text":"Bestilling skal inneholde bestillingsnummer, enhet/kontakt, kundenummer og leveringssted.",
                    "source_file":src_file,"source_row":"Bestilling"})
    if re.search(r"avbestille.*30\s*dagers\s*varsel", t, re.I):
        TERMS["cancellation:notice_days_for_calloff"] = 30; rc_term("cancellation:notice_days_for_calloff",30)
    if re.search(r"gebyr\s+p[åa]\s*4\s*\(\s*fire\s*\)\s*prosent", t, re.I):
        TERMS["cancellation:fee_pct_of_assignment"] = 4; rc_term("cancellation:fee_pct_of_assignment",4)

    # Statistics (cadence + LD)
    if re.search(r"Kvartalsvis statistikk.*20\.04.*05\.08.*20\.10.*20\.01", t, re.I):
        TERMS["stats:quarterly_due_dates"] = "20.04;05.08;20.10;20.01"; rc_term("stats:quarterly_due_dates",TERMS["stats:quarterly_due_dates"])
    if re.search(r"Dagmulkten.*kr\s*1\s*000\s*per\s*arbeidsdag.*statistikk", t, re.I):
        TERMS["stats:delay_ld_nok_per_working_day"] = 1000; rc_term("stats:delay_ld_nok_per_working_day",1000)
    if re.search(r"leverandor\.sykehusinnkjop\.no", t, re.I):
        TERMS["stats:portal_url"] = "https://leverandor.sykehusinnkjop.no"; rc_term("stats:portal_url",TERMS["stats:portal_url"])

    # Price / indexation
    if re.search(r"Prisene\s+er\s+faste\s+i\s*12\s*måneder", t, re.I):
        TERMS["price:fixed_first_months"] = 12; rc_term("price:fixed_first_months",12)
    if re.search(r"varsles.*2\s*måneder før", t, re.I):
        TERMS["price:kpi_notice_weeks"] = 8; rc_term("price:kpi_notice_weeks",8)
    m = re.search(r"Førstegangs.*100%\s+av\s+endringen\s+i\s+KPI.*fra\s+mars\s+(\d{4})", t, re.I)
    if m:
        TERMS["price:kpi_first_fraction_pct"] = 100; rc_term("price:kpi_first_fraction_pct",100)
        TERMS["price:kpi_first_reference_month"] = f"{m.group(1)}-03"; rc_term("price:kpi_first_reference_month",TERMS["price:kpi_first_reference_month"])
    if re.search(r"Etterfølgende.*100%\s+av\s+endringen\s+i\s+KPI", t, re.I):
        TERMS["price:kpi_subsequent_fraction_pct"] = 100; rc_term("price:kpi_subsequent_fraction_pct",100)
    if re.search(r"justeres ikke.*valutakurs", t, re.I):
        TERMS["price:currency_adjustment_allowed"] = False; rc_term("price:currency_adjustment_allowed",False)
    m = re.search(r"myndighetsvedtak.*netto\s+utgjør\s+mer\s+enn\s*([0-9]+)\s*%", t, re.I)
    if m:
        TERMS["price:authority_change_threshold_pct"] = int(m.group(1)); rc_term("price:authority_change_threshold_pct", int(m.group(1)))

    # Invoicing / payment
    if re.search(r"fakturering\s+skje\s+månedlig", t, re.I):
        TERMS["invoice:frequency"] = "monthly"; rc_term("invoice:frequency","monthly")
    if re.search(r"Betalingsfrist\s+er\s*30\s*dager", t, re.I):
        TERMS["payment:days"] = 30; rc_term("payment:days",30)
    if re.search(r"ikke\s+beregnes.*gebyr", t, re.I):
        TERMS["invoice:fee_prohibited"] = True; rc_term("invoice:fee_prohibited",True)
    if re.search(r"gebyr\s+tilsvarende\s+NOK\s*500\s*pr\s*faktura", t, re.I):
        TERMS["invoice:wrong_invoice_fee_nok"] = 500; rc_term("invoice:wrong_invoice_fee_nok",500)

    # Delay – dagmulkt regime
    if re.search(r"Dagmulkten.*1\s*%\s*per\s*virkedag", t, re.I):
        TERMS["delay:ld_rate_pct_per_working_day"] = 1.0; rc_term("delay:ld_rate_pct_per_working_day",1.0)
    if re.search(r"eller\s*kr\s*1000", t, re.I):
        TERMS["delay:ld_min_nok_per_day"] = 1000; rc_term("delay:ld_min_nok_per_day",1000)
    if re.search(r"Dagmulktperioden\s+er\s+begrenset\s+til\s*100\s*virkedager", t, re.I):
        TERMS["delay:ld_max_working_days"] = 100; rc_term("delay:ld_max_working_days",100)

    # Force majeure
    if re.search(r"75\s*kalenderdager.*15\s*kalenderdagers\s*varsel", t, re.I):
        TERMS["force_majeure:termination_days"] = 75; rc_term("force_majeure:termination_days",75)
        TERMS["force_majeure:notice_days"]   = 15; rc_term("force_majeure:notice_days",15)

    # Marketing penalty
    if re.search(r"bot\s+p[åa]\s*0,?2\s*%.*eller\s*10\s*000", t, re.I):
        TERMS["marketing:penalty_pct"] = 0.2; rc_term("marketing:penalty_pct",0.2)
        TERMS["marketing:penalty_min_nok"] = 10000; rc_term("marketing:penalty_min_nok",10000)

    # Sanctions / privacy
    if re.search(r"internasjonale\s+sanksjoner", t, re.I):
        TERMS["compliance:sanctions_clause"] = True; rc_term("compliance:sanctions_clause",True)
    if re.search(r"databehandleravtale|databehandler", t, re.I):
        TERMS["privacy:dpa_required_if_processing"] = True; rc_term("privacy:dpa_required_if_processing",True)

    # Admin requirements (structure)
    if re.search(r"avtaleforvalters\s+portal.*leverandor\.sykehusinnkjop\.no", t, re.I):
        REQ.append({"req_id":"STAT-PORTAL","section":"Rapportering","kind":"mandatory","prompt_kind":"attachment",
                    "value_hint":"portalbruker + mal",
                    "krav_text":"Kvartalsstatistikk leveres via avtaleforvalters portal på oppgitt mal; leverandør må opprette bruker.",
                    "source_file":src_file,"source_row":"Statistikk"})
    if re.search(r"årlig\s+status.*(evalueringsmøte|statusmøte)", t, re.I):
        REQ.append({"req_id":"MOTE-STATUS","section":"Kommunikasjon","kind":"mandatory","prompt_kind":"boolean",
                    "value_hint":"årlig",
                    "krav_text":"Minst ett årlig status-/evalueringsmøte; øvrige møter med 5 virkedagers varsel.",
                    "source_file":src_file,"source_row":"Møter"})

    return TERMS, REQ, RC


# ---------------- AKRIM (Bilag 3) — compliance terms ----------------
def extract_renhold_akrim(text: str, src_file: str):
    """Return (terms:dict, req_rows:list, receipts:list) from 'Bilag 3 Krav akrim Renhold'."""
    t = text
    TERMS: dict = {}
    REQ:   list = []
    RC:    list = []

    def rc(k,v): RC.append({"type":"contract_term","key":k,"value":v,"source_file":src_file})
    def R(req_id, section, kind, pk, hint, txt, row):
        REQ.append({"req_id":req_id,"section":section,"kind":kind,"prompt_kind":pk,"value_hint":hint,
                    "krav_text":txt,"source_file":src_file,"source_row":row})

    # Underleverandør-kjede: maks 2 ledd (heving mulig; "samme bestemmelser i alle avtaler")
    if re.search(r"ikke.*flere enn to ledd underleverand", t, re.I):
        TERMS["subchain:max_levels"] = 2; rc("subchain:max_levels", 2)
        TERMS["subchain:flowdown_required"] = True; rc("subchain:flowdown_required", True)
        TERMS["subchain:heving_on_material_breach"] = True; rc("subchain:heving_on_material_breach", True)

    # OTP (obligatorisk tjenestepensjon): krav + dokumentasjon + dagbot + tilbakehold + heving/utskifting
    if re.search(r"obligatorisk\s+tjenestepensjon|OTP", t, re.I):
        TERMS["otp:required"] = True; rc("otp:required", True)
        TERMS["otp:doc_on_request"] = True; rc("otp:doc_on_request", True)
        TERMS["otp:doc_daybot_nok_per_day"] = 1500; rc("otp:doc_daybot_nok_per_day", 1500)
        TERMS["otp:withhold_twice_saving"] = True; rc("otp:withhold_twice_saving", True)
        TERMS["otp:heving_on_material_breach"] = True; rc("otp:heving_on_material_breach", True)
        TERMS["otp:replace_sub_on_breach"] = True; rc("otp:replace_sub_on_breach", True)
        R("AKRIM-OTP-FLOWDOWN","AKRIM/OTP","mandatory","attachment","flowdown i alle avtaler",
          "Alle avtaler leverandøren inngår for arbeid under kontrakten skal inneholde tilsvarende OTP-bestemmelser.",
          "Bilag 3 – OTP")

    # HMS-kort: påkrevd (bortvisning uten kort)
    if re.search(r"HMS[-\s]?kort.*b[øo]r?tvist|bortvist", t, re.I) or re.search(r"HMS[-\s]?kort", t, re.I):
        TERMS["hms_card:required_visible"] = True; rc("hms_card:required_visible", True)
        TERMS["hms_card:no_card_ban"] = True; rc("hms_card:no_card_ban", True)

    # Lærlinger: krav for kontrakter > 2,05 MNOK eks mva og varighet > 3 mnd
    if re.search(r"l[æa]rling.*2,?0?5\s*mill", t, re.I) or re.search(r"2\.?05\s*millioner", t, re.I):
        TERMS["apprentice:required_if_value_mnok"] = 2.05; rc("apprentice:required_if_value_mnok", 2.05)
        TERMS["apprentice:required_if_months_gt"] = 3; rc("apprentice:required_if_months_gt", 3)
        TERMS["apprentice:eu_ees_accepted"] = True; rc("apprentice:eu_ees_accepted", True)
        TERMS["apprentice:hours_report_at_end"] = True; rc("apprentice:hours_report_at_end", True)
        TERMS["apprentice:exception_if_proven_attempts"] = True; rc("apprentice:exception_if_proven_attempts", True)
        TERMS["apprentice:buyer_control_and_remedy"] = True; rc("apprentice:buyer_control_and_remedy", True)

    # Lønn via bank (kontantforbud): dokumentasjon + dagbot + tilbakehold + heving + utskifting
    if re.search(r"betaling.*via\s*bank|til\s*konto i bank", t, re.I):
        TERMS["wages:paid_via_bank_required"] = True; rc("wages:paid_via_bank_required", True)
        TERMS["wages:doc_required"] = True; rc("wages:doc_required", True)
        TERMS["wages:doc_daybot_nok_per_day"] = 1500; rc("wages:doc_daybot_nok_per_day", 1500)
        TERMS["wages:withhold_twice_cash"] = True; rc("wages:withhold_twice_cash", True)
        TERMS["wages:heving_on_material_breach"] = True; rc("wages:heving_on_material_breach", True)
        TERMS["wages:replace_sub_on_breach"] = True; rc("wages:replace_sub_on_breach", True)

    # Renholdsregisteret: registreringsplikt
    if re.search(r"renholdsregister", t, re.I):
        TERMS["renholdsregister:registration_required"] = True; rc("renholdsregister:registration_required", True)
        R("AKRIM-RENHOLDSREGISTER","AKRIM/Registrering","mandatory","boolean","registrert",
          "Leverandør og underleverandører av renholdstjenester skal være registrert i renholdsregisteret under hele kontraktsperioden.",
          "Bilag 3 – Registreringsplikt")

    return TERMS, REQ, RC

# ---------------- AKRIM self-report (Bilag 4) ----------------
def extract_renhold_akrim_selfreport(text: str, src_file: str):
    """
    Return (terms: dict, req_rows: list, receipts: list) from 'Bilag 4 Egenrapportering akrim Renhold'.
    Captures: initial due (30 days after signature), recurring allowed, scope (employees/hired/posted/subs),
              flow-down, NO-PII gate, and a structured set of mandatory confirmations (as typed requirements).
    """
    import re
    t = text
    TERMS: dict = {}
    REQ:   list = []
    RC:    list = []

    def rc_term(k,v): RC.append({"type":"contract_term","key":k,"value":v,"source_file":src_file})
    def R(req_id, section, kind, pk, hint, txt, row):
        REQ.append({"req_id":req_id,"section":section,"kind":kind,"prompt_kind":pk,"value_hint":hint,
                    "krav_text":txt,"source_file":src_file,"source_row":row})

    # Initial deadline within one month after signature; can be required multiple times (Bilag 4, ingress)
    if re.search(r"innen\s+én\s+mån(e|å)d\s+etter\s+.*signert", t, re.I):
        TERMS["akrim:selfreport_initial_due_days"] = 30; rc_term("akrim:selfreport_initial_due_days", 30)
    if re.search(r"kan\s+kreves\s+flere\s+ganger", t, re.I):
        TERMS["akrim:selfreport_recurring"] = True; rc_term("akrim:selfreport_recurring", True)

    # Scope includes own + hired + posted + subs; flow-down (Bilag 4, ingress)
    if re.search(r"ansatte.*innleide.*utsendte.*underleverand", t, re.I|re.S):
        TERMS["akrim:scope_employees"]       = True; rc_term("akrim:scope_employees", True)
        TERMS["akrim:scope_hired"]           = True; rc_term("akrim:scope_hired", True)
        TERMS["akrim:scope_posted"]          = True; rc_term("akrim:scope_posted", True)
        TERMS["akrim:scope_subcontractors"]  = True; rc_term("akrim:scope_subcontractors", True)
    if re.search(r"underleverand[øo]rer.*skal\s+også\s+fylle\s+ut\s+samme\s+skjema", t, re.I):
        TERMS["akrim:selfreport_flowdown_required"] = True; rc_term("akrim:selfreport_flowdown_required", True)

    # NO PII rule (Bilag 4, avslutning)
    if re.search(r"skal\s+ikke\s+vedlegges\s+personopplysninger|personopplysninger\s+sladdes", t, re.I):
        R("AKRIM-NO-PII","Egenrapportering","mandatory","boolean","ingen PII",
          "Vedlegg/rapporter skal ikke inneholde personopplysninger; ev. PII skal sladdes.", "Bilag 4")

    # Company / contract info (structure gates)
    R("AKRIM-ORG","Selskapsinformasjon","mandatory","attachment","orgnr/registreringsland",
      "Oppgi leverandørnavn, organisasjonsnummer og registreringsland.", "Bilag 4 – Informasjon")
    R("AKRIM-KONTR","Selskapsinformasjon","mandatory","attachment","kontraktsnr/navn/varighet",
      "Oppgi kontrakts-/avtalenummer, navn og varighet.", "Bilag 4 – Informasjon")
    R("AKRIM-BESK","Selskapsinformasjon","mandatory","attachment","selskapsform/eier/organisering/omsetning/stiftelsesdato/orgnr",
      "Beskriv virksomheten (form, eiere, organisering, omsetning, stiftelsesdato, org.nr.).", "Bilag 4 – Selskapsinformasjon")
    R("AKRIM-NACE","Selskapsinformasjon","mandatory","attachment","næringskoder",
      "Oppgi næringskoder (NACE).", "Bilag 4 – Selskapsinformasjon")
    R("AKRIM-RENHOLDSREGISTER","Registrering","mandatory","boolean","registrert",
      "Bekreft og redegjør for registrering i Renholdsregisteret for leverandør og underleverandører.", "Bilag 4 – Selskapsinformasjon")

    # Contract work info
    R("AKRIM-EMP-COUNT","Kontraktsarbeid","mandatory","attachment","ansatte + % utenlandske",
      "Oppgi antall ansatte og andel utenlandske arbeidstakere.", "Bilag 4 – Kontraktsarbeid")
    R("AKRIM-POSTED","Kontraktsarbeid","mandatory","boolean","utsendt arbeidskraft",
      "Oppgi om utsendt arbeidskraft benyttes.", "Bilag 4 – Kontraktsarbeid")
    R("AKRIM-HIRED","Kontraktsarbeid","mandatory","attachment","innleie + L&A ivaretakelse",
      "Oppgi om innleid arbeidskraft benyttes; beskriv omfang og hvordan L&A ivaretas.", "Bilag 4 – Kontraktsarbeid")
    R("AKRIM-TRADES","Kontraktsarbeid","mandatory","attachment","fagområder",
      "Oppgi fagområder som utføres på kontrakten.", "Bilag 4 – Kontraktsarbeid")

    # Tariff, worktime rules, benefits, representation
    R("AKRIM-TARIFF","Lønn/arbeidsvilkår","mandatory","attachment","tariffavtaler (lenker)",
      "Oppgi tariffavtaler som legges til grunn (lenker).", "Bilag 4 – L&A")
    R("AKRIM-WT-SPES","Lønn/arbeidsvilkår","mandatory","attachment","særregler arbeidstid",
      "Oppgi særregler/avtaler om arbeidstid utover AML/tariff; vedlegg lenke/kopi.", "Bilag 4 – L&A")
    R("AKRIM-LODGING","Lønn/arbeidsvilkår","mandatory","boolean","kost/losji",
      "Oppgi om virksomheten dekker kost og losji.", "Bilag 4 – L&A")
    R("AKRIM-UNION","Representasjon","mandatory","boolean","tillitsvalgte",
      "Oppgi om ansatte har tillitsvalgte.", "Bilag 4 – Representasjon")
    R("AKRIM-VO","Representasjon","mandatory","boolean","verneombud/regionale VO",
      "Oppgi om ansatte har verneombud (evt. regionalt).", "Bilag 4 – Representasjon")

    # Subcontractors list (structure; no PII)
    R("AKRIM-UL-LISTE","Underleverandører","mandatory","attachment","navn/orgnr/nasjonalitet",
      "List opp underleverandører (inkl. bemanningsbyråer) med navn, org.nr. og nasjonalitet (ingen PII).", "Bilag 4 – L&A")

    # AML §§14-5/14-6 written contracts
    R("AKRIM-AML-AVT","Arbeidsavtaler","mandatory","boolean","AML §§14-5/14-6",
      "Bekreft skriftlig arbeidsavtale på morsmål/språk de behersker; minstekrav AML §§14-5/14-6.", "Bilag 4 – L&A")

    # OTP, HMS-kort, wages via bank (confirmations)
    R("AKRIM-OTP","OTP","mandatory","attachment","OTP-oppfyllelse",
      "Redegjør for oppfyllelse av OTP for alle som medvirker.", "Bilag 4 – L&A")
    R("AKRIM-HMSKORT","HMS-kort","mandatory","attachment","gyldig HMS-kort",
      "Redegjør for HMS-kort for alle som medvirker; søknadsskjema aksepteres ikke.", "Bilag 4 – L&A")
    R("AKRIM-WAGES-BANK","Lønn via bank","mandatory","attachment","bankkonto",
      "Redegjør for at lønn og godtgjørelse utbetales til konto i bank/betalingsforetak.", "Bilag 4 – L&A")

    # Inspections / orders / prosecutions
    R("AKRIM-TILSYN","Tilsyn","mandatory","attachment","dokumentasjon",
      "Oppgi tilsyn fra Arbeidstilsynet siste 2 år; legg ved dokumentasjon.", "Bilag 4 – Tilsyn/pålegg")
    R("AKRIM-PÅLEGG","Pålegg","mandatory","attachment","vedtak + rettetiltak",
      "Legg ved vedtak om pålegg + beskriv rettetiltak.", "Bilag 4 – Tilsyn/pålegg")
    R("AKRIM-ANMELDT","Reaksjoner","mandatory","attachment","dokumentasjon",
      "Oppgi ev. anmeldelse/domfellelse relatert til AKRIM/sosial dumping/L&A; vedlegg dokumentasjon.", "Bilag 4 – Reaksjoner")

    return TERMS, REQ, RC

# ---------------- Experience form (Vedlegg 2 – Svarskjema erfaring) ----------------
def extract_renhold_experience(text: str, src_file: str):
    """
    Structure-only gates for the references form. We do NOT extract any PII.
    Emits requirements such as:
      - Provide at least 3 references (Leveranse 1–3 blocks present)
      - Each reference must include: customer/firm name, contact person, phone, value, time, sector, description.
    """
    t = text
    REQ = []
    RC  = []

    def R(req_id, section, kind, pk, hint, txt, row):
        REQ.append({
            "req_id": req_id, "section": section, "kind": kind, "prompt_kind": pk,
            "value_hint": hint, "krav_text": txt, "source_file": src_file, "source_row": row
        })

    # Detect presence of the three reference blocks (no PII captured)
    has_l1 = bool(re.search(r"Leveranse\s*1", t, re.I))
    has_l2 = bool(re.search(r"Leveranse\s*2", t, re.I))
    has_l3 = bool(re.search(r"Leveranse\s*3", t, re.I))
    if has_l1 and has_l2 and has_l3:
        R("EXP-COUNT-3", "Erfaring/referanser", "mandatory", "attachment", "3 referanser",
          "Leverandøren skal levere 3 referanser (Leveranse 1–3) på skjemaet.", "Form – Leveranse 1–3")

    # Field structure (we only gate that these fields must be filled per reference)
    fields_required = [
        "Firmanavn, kunde",
        "Kontaktperson hos kunde",
        "Telefonnummer",
        "Leveransens verdi",
        "Leveransens tidspunkt",
        "Offentlig eller privat kunde",
        "Beskrivelse av leveransen"
    ]
    if all(re.search(re.escape(f), t, re.I) for f in fields_required):
        R("EXP-FIELD-SET", "Erfaring/referanser", "mandatory", "boolean", "felt satt (struktur)",
          "Hver referanse skal inneholde: kunde, kontaktperson, telefonnummer, verdi, tidspunkt, offentlig/privat, og beskrivelse.", "Form – felter")

    # Signature/date placeholders (structure)
    if re.search(r"Underskrift", t, re.I):
        R("EXP-SIGN", "Erfaring/referanser", "mandatory", "attachment", "signert/datert",
          "Skjema skal signeres og dateres.", "Form – signatur/dato")

    # No-PII policy note (structure gate – we do not store names/numbers)
    R("EXP-NO-PII", "Erfaring/referanser", "mandatory", "boolean", "PCC lagrer ikke PII",
      "PCC kontrollerer kun at feltene finnes; navn/telefonnummer lagres ikke i matriser.", "Personvern")

    return REQ, RC
