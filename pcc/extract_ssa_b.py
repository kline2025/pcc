import re
from typing import Dict, List, Tuple

def extract_ssa_b_contract(text: str, src_file: str) -> Tuple[Dict, List[Dict], List[Dict]]:
    """
    SSA-B – Generell avtaletekst (2015)
    Returns: (terms, req_rows, receipts)
    """
    t = text
    TERMS: Dict[str, object] = {}
    REQ:   List[Dict] = []
    RC:    List[Dict] = []

    def term(k,v,snip=""): TERMS[k]=v; RC.append({"type":"contract_term","key":k,"value":v,"source_file":src_file,"snippet":snip})

    # Family
    term("contract:family","SSA-B","SSA-B 2015 – Generell avtaletekst")

    # Endring/stans/avbestilling (pkt. 2)
    if re.search(r"Endringer.*skal avtales skriftlig", t, re.I):
        term("change:written_required", True, "Pkt. 2.1")
    if re.search(r"stanses.*minimum\s*5\s*kalenderdager", t, re.I):
        term("suspension:customer_notice_days", 5, "Pkt. 2.2")
    if re.search(r"Avbestilling.*30\s*\(tretti\)\s*dagers", t, re.I):
        term("termination:customer_cancel_notice_days", 30, "Pkt. 2.3")

    # Vederlag/fakturering/betaling/EHF (pkt. 4)
    if re.search(r"Fakturering.*etterskuddsvis", t, re.I):
        term("invoice:postpaid_monthly_default", True, "Pkt. 4.2")
    if re.search(r"Betaling.*30\s*\(tretti\)\s*kalenderdager", t, re.I):
        term("payment:days", 30, "Pkt. 4.2")
    if re.search(r"elektronisk\s*faktura.*godkjent standardformat", t, re.I):
        term("invoice:ehf_required", True, "Pkt. 4.2")
    if re.search(r"Prisene.*kan endres.*konsumprisindeks", t, re.I):
        term("price:indexation","KPI_yearly", "Pkt. 4.5")

    # Opphavs-/eiendomsrett (pkt. 5)
    if re.search(r"rettigheter til resultater.*tilfaller Kunden", t, re.I):
        term("ip:result_ownership_customer", True, "Pkt. 5")

    # Mislighold/sanksjoner (pkt. 6)
    if re.search(r"prisavslag", t, re.I):
        term("remedy:price_reduction", True, "Pkt. 6.3.2")
    if re.search(r"indirekte\s+tap.*kan ikke kreves", t, re.I):
        term("liability:indirect_excluded", True, "Pkt. 6.3.5")
    if re.search(r"Samlet erstatning.*begrenset.*avtalt vederlag|øvre estimat", t, re.I):
        term("liability:cap_basis","contract_amount_or_estimate", "Pkt. 6.3.5")

    # Lønns- og arbeidsvilkår (pkt. 3.2)
    if re.search(r"allmenngjort tariffavtale|landsomfattende tariffavtale", t, re.I):
        term("labour:compliance_required", True, "Pkt. 3.2")
    if re.search(r"holde tilbake.*ca\.\s*2\s*\(to\)\s*ganger", t, re.I):
        term("labour:retention_multiplier_x2", True, "Pkt. 3.2")

    # Taushetsplikt (pkt. 3.6) – fem år etter leveringsdag
    if re.search(r"taushetsplikten.*opp[høø]rer\s*fem\s*\(5\)\s*år\s*etter\s*leveringsdag", t, re.I):
        term("confidentiality:term_years_after_delivery", 5, "Pkt. 3.6")

    # Skriftlighet (pkt. 3.7)
    if re.search(r"Alle varsler.*skal gis skriftlig", t, re.I):
        term("communications:written_required", True, "Pkt. 3.7")

    # Rettsvalg/tvister (pkt. 8)
    if re.search(r"rettigheter.*bestemmes.*norsk rett", t, re.I):
        term("law:governing_law","NO", "Pkt. 8.1")
    if re.search(r"Kundens hjemting er verneting", t, re.I):
        term("law:venue","customer_home_court", "Pkt. 8.4")

    return TERMS, REQ, RC


def extract_ssa_b_bilag(text: str, src_file: str) -> Tuple[List[Dict], List[Dict]]:
    """
    SSA-B – Bilag (2015) – structure-only gates for bilag 1–6 and admin fields.
    Returns: (req_rows, receipts)
    """
    t = text
    REQ: List[Dict] = []
    RC:  List[Dict] = []

    def R(req_id, section, kind, pk, hint, txt, row):
        REQ.append({"req_id":req_id,"section":section,"kind":kind,"prompt_kind":pk,
                    "value_hint":hint,"krav_text":txt,"source_file":src_file,"source_row":row})

    # Bilag presence requirements
    for num, label in [("1","Beskrivelse av bistanden"), ("2","Prosjekt- og fremdriftsplan"),
                       ("3","Administrative bestemmelser"), ("4","Pris og prisbestemmelser"),
                       ("5","Endringer i generell avtaletekst"), ("6","Endringer etter avtaleinngåelsen")]:
        R(f"SSA-B-BILAG-{num}", "SSA-B bilag", "mandatory", "attachment",
          f"Bilag {num} utfylt", f"Bilag {num}: {label} skal fylles ut og vedlegges.",
          f"Bilag {num}")

    # Admin contact roles + nøkkelpersonell in bilag 3
    R("SSA-B-ADMIN-CONTACT","SSA-B bilag","mandatory","value",
      "partenes representanter","Angi bemyndigede representanter (Bilag 3).","Bilag 3")
    R("SSA-B-KEY-STAFF","SSA-B bilag","mandatory","value",
      "nøkkelpersonell","Oppgi nøkkelpersonell og utskiftingsprosedyrer (Bilag 3).","Bilag 3")

    # Price sheet in bilag 4 + timespec
    R("SSA-B-PRICE","SSA-B bilag","mandatory","attachment",
      "bilag 4 – pris og prisbestemmelser",
      "Før priser, faktureringsregime og ev. indeksering i Bilag 4. Timespesifikasjon vedlegges løpende fakturaer.",
      "Bilag 4")

    return REQ, RC
