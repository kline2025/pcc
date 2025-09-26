import re
from typing import Dict, List, Tuple

def _term(TERMS, RC, k, v, src, snip=""):
    TERMS[k] = v
    RC.append({"type":"contract_term","key":k,"value":v,"source_file":src,"snippet":snip})

def _req(REQ, req_id, section, kind, pk, hint, txt, src, row):
    REQ.append({"req_id":req_id,"section":section,"kind":kind,"prompt_kind":pk,
                "value_hint":hint,"krav_text":txt,"source_file":src,"source_row":row})

def extract_dpa2020_contract(text: str, src_file: str) -> Tuple[Dict, List[Dict], List[Dict]]:
    """
    Databehandleravtale – Generell avtaletekst versjon 2020 (nøytral mal).
    Returns: (terms, req_rows, receipts)
    """
    t = text
    TERMS: Dict[str, object] = {}
    REQ:   List[Dict] = []
    RC:    List[Dict] = []

    _term(TERMS, RC, "privacy:dpa_template", "Generic v2020", src_file, "Versjon 01.2020")

    # Roller & forrang
    if re.search(r"Behandlingsansvarlig.*Databehandler", t, re.I):
        _term(TERMS, RC, "privacy:roles_declared", True, src_file, "Formål/definisjoner")
    if re.search(r"Databehandleravtalen har forrang.*personopplysninger", t, re.I):
        _term(TERMS, RC, "privacy:dpa_precedence_over_master", True, src_file, "Forrang mot Hovedavtalen")

    # Sikkerhet, bruddvarsling, revisjon
    if re.search(r"egnete tekniske og organisatoriske tiltak", t, re.I):
        _term(TERMS, RC, "security:toms_required", True, src_file, "Pkt. 7")
    if re.search(r"uten ugrunnet opphold.*(varsle|underrette).*brudd", t, re.I):
        _term(TERMS, RC, "privacy:breach_notice_without_delay", True, src_file, "Pkt. 8")
    if re.search(r"inspeksjoner og revisjoner", t, re.I):
        _term(TERMS, RC, "privacy:audit_rights_present", True, src_file, "Pkt. 11")

    # Underdatabehandlere (flowdown/list/notice)
    if re.search(r"tilsvarende forpliktelser.*Underdatabehandler", t, re.I):
        _term(TERMS, RC, "privacy:subprocessor_flowdown", True, src_file, "Pkt. 9")
    if re.search(r"oversikt over godkjente Underdatabehandlere", t, re.I):
        _term(TERMS, RC, "privacy:subprocessor_list_required", True, src_file, "Pkt. 9")
    if re.search(r"informere.*(skifte|endringer).*Underdatabehandler", t, re.I):
        _term(TERMS, RC, "privacy:subprocessor_change_notice_required", True, src_file, "Pkt. 9")

    # Overføring utenfor EØS – samtykke + lovlige mekanismer
    if re.search(r"bare overf[øo]res.*utenfor EØS.*skriftlig.*godkjent", t, re.I):
        _term(TERMS, RC, "privacy:third_country_transfer_requires_consent", True, src_file, "Pkt. 10")
    if re.search(r"artikkel 45|artikkel 46.*EU Model clauses|artikkel 47", t, re.I):
        _term(TERMS, RC, "privacy:third_country_transfer_mechanisms", "Art.45/46/47", src_file, "Pkt. 10")

    # Sletting/tilbakelevering
    if re.search(r"tilbakelevere.*slette.*ved opph[øo]r", t, re.I):
        _term(TERMS, RC, "privacy:return_then_delete_required", True, src_file, "Pkt. 12")

    return TERMS, REQ, RC


def extract_dpa2020_bilag(text: str, src_file: str) -> Tuple[List[Dict], List[Dict]]:
    """
    Bilag A–D – strukturkrav (må fylles ut)
    Returns: (req_rows, receipts)
    """
    t = text
    REQ: List[Dict] = []
    RC:  List[Dict] = []

    # Bilag A – behandlingen
    if re.search(r"Bilag\s*A.*Opplysninger om behandlingen", t, re.I):
        _req(REQ, "DPA-A", "DPA Bilag", "mandatory", "attachment",
             "Bilag A utfylt (formål, typer opplysninger, registrerte, varighet)",
             "Fyll ut Bilag A (formål/typer/varighet).", src_file, "Bilag A")

    # Bilag B – underdatabehandlere + varslingsregime
    if re.search(r"Bilag\s*B.*Underdatabehandlere", t, re.I):
        _req(REQ, "DPA-B", "DPA Bilag", "attachment", "liste + endringsregime",
             "Før opp godkjente underdatabehandlere og varslingsregime for endringer (Bilag B).",
             src_file, "Bilag B")

    # Bilag C – instruks og sikkerhet; lokasjoner; revisjon
    if re.search(r"Bilag\s*C.*Instruks", t, re.I):
        _req(REQ, "DPA-C", "DPA Bilag", "attachment", "TOMs + lokasjoner + revisjon",
             "Angi TOMs, lokasjoner (tilgang/lagring/prosessering), revisjonsrutiner (Bilag C).",
             src_file, "Bilag C")

    # Bilag D – endringer/logg
    if re.search(r"Bilag\s*D.*Endringer", t, re.I):
        _req(REQ, "DPA-D", "DPA Bilag", "attachment", "endringslogg",
             "Før avtalte endringer i Bilag D (standardtekst og senere endringer).",
             src_file, "Bilag D")

    return REQ, RC
