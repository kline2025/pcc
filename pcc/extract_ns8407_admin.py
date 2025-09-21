import re
from typing import List, Dict, Tuple

def _rt(req_id, section, kind, prompt_kind, value_hint, krav_text, src, src_row):
    return {"req_id":req_id,"section":section,"kind":kind,"prompt_kind":prompt_kind,
            "value_hint":value_hint,"krav_text":krav_text,"source_file":src,"source_row":src_row}

def _cleannum(s:str)->int:
    s=(s or "").replace(" ", "").replace("\u00A0","").replace(".","").replace(",","")
    m=re.search(r"(\d+)",s); return int(m.group(1)) if m else 0

def extract_forretningsrutiner(text:str, src_file:str)->Tuple[Dict,List[Dict],List[Dict]]:
    """Return (contract_terms, req_rows, receipts) from IIS8 Forretningsrutiner (NS 8407)."""
    TERMS: Dict[str,object] = {}
    REQ: List[Dict] = []
    RC: List[Dict] = []
    t=text

    # 1) Korrespondanse (header format)
    if re.search(r"Elektroniske brev.*overskrift", t, re.I):
        TERMS["process:correspondence_header"]="1004914 Eksternt kontrollsenter for post og varer – K210 Totalentreprise – <sak/emne>"
        REQ.append(_rt("ADM-KORR-HDR","Kommunikasjon","mandatory","attachment",
                       "header/emnefelt","Bruk fast overskrift/emne i elektronisk korrespondanse som angitt.",src_file,"§1"))

    # 2) Endringsprosesser (EF/EO/R/VK/BH/EA) and authorization cap
    if re.search(r"Endringsforespørsel|\bEF-skjema\b",t,re.I): REQ.append(_rt("END-EF","Endringsprosess","mandatory","attachment","EF-skjema","Bruk EF-skjema for å hente inn tilbud før bestilling.",src_file,"§2.3"))
    if re.search(r"Endringsordre|\bEO-skjema\b",t,re.I):     REQ.append(_rt("END-EO","Endringsprosess","mandatory","attachment","EO-skjema","Bruk EO-skjema når endring pålegges før pris/frist er avklart.",src_file,"§2.4"))
    if re.search(r"Rekvisisjon|\bR-skjema\b",t,re.I):        REQ.append(_rt("END-R","Endringsprosess","mandatory","attachment","R-skjema","Bruk R-skjema ved mindre endringer innen fullmakt.",src_file,"§2.5"))
    if re.search(r"Totalentreprenørens skjema|VK-skjema",t,re.I): REQ.append(_rt("END-VK","Varsel/krav (TE)","mandatory","attachment","VK-skjema","TE varsler krav/frist/irregulær endring med VK-skjema.",src_file,"§2.6"))
    if re.search(r"Byggherrens svar|BH-skjema",t,re.I):      REQ.append(_rt("END-BH","Svar byggherre","mandatory","attachment","BH-skjema","PL/BHO svarer på VK med BH-skjema.",src_file,"§2.7"))
    if re.search(r"Endringsavtale|\bEA-skjema\b",t,re.I):    REQ.append(_rt("END-EA","Forlik/endringsavtale","mandatory","attachment","EA-skjema","EA-skjema ved enighet om arbeid/vederlag/frist.",src_file,"§2.9"))

    m=re.search(r"BHO.*R[- ]skjema.*?inn til\s*kr\s*([0-9\s.,]+)", t, re.I)
    if m:
        TERMS["change:client_r_auth_cap_nok"]= _cleannum(m.group(1))
        RC.append({"type":"contract_term","key":"change:client_r_auth_cap_nok","value":TERMS["change:client_r_auth_cap_nok"],"source_file":src_file})

    # 3) Modell- og tegningshåndtering
    if re.search(r"BIM-gjennomføringsplan",t,re.I):
        REQ.append(_rt("ADM-BIM-OVERSIKT","Modellhåndtering","mandatory","attachment","modelloversikt i BEP",
                       "TE vedlikeholder oversikt over etablerte modeller i Avtalt BEP og distribuerer godkjente revisjoner.",src_file,"§3.1–3.2"))
    if re.search(r"NS\s*8310",t,re.I):
        TERMS["drawings:rev_marking_standard"]="NS 8310:1983"
        RC.append({"type":"contract_term","key":"drawings:rev_marking_standard","value":"NS 8310:1983","source_file":src_file})
        REQ.append(_rt("ADM-TEGN-DISTR","Tegningshåndtering","mandatory","attachment","tegnings-/distribusjonsliste",
                       "TE fører tegnings-/distribusjonsliste; oppdatert tegningsliste følger hver forsendelse; foreldede tegninger inndras.",src_file,"§4"))

    # 4) Fakturering og økonomi
    if re.search(r"Faktura.*EHF|statsbygg\.no/faktura",t,re.I): TERMS["invoice:electronic_required"]=True
    if re.search(r"aksepterer ikke.*faktura.?gebyr",t,re.I): TERMS["invoice:fee_prohibited"]=True
    REQ.append(_rt("ADM-AVDRAG","Fakturering","mandatory","attachment","avdragsfaktura innhold",
                   "Avdragsfaktura skal inneholde prosjektnr, kontraktsnr, bestillingsnr (vedlagt), referanse ID, beløpslinjer m.m.",src_file,"§5.2"))
    REQ.append(_rt("ADM-END-BEST","Fakturering","mandatory","attachment","separat fakturering endringer",
                   "Bestillinger utover kontraktssum faktureres separat iht bestilling; dokumentasjon vedlegges.",src_file,"§5.3"))
    REQ.append(_rt("ADM-LPS","Fakturering","mandatory","attachment","LPS-faktura egen",
                   "LPS (lønn/prisstigning) faktureres separat når indeks foreligger; grunnlag som angitt.",src_file,"§5.4"))

    # 5) Møter og referater
    REQ.append(_rt("MTG-PLAN","Møteplan","mandatory","boolean","møteplan + referat ≤5 d",
                   "Utarbeid møteplan; referater sendes innen 5 dager etter møte via distribusjonsliste.",src_file,"§6"))
    REQ.append(_rt("MTG-BYGGHERRE","Byggherremøter","mandatory","boolean","BH innkaller; TE møteplikt","BH innkaller; referat føres av BH.",src_file,"§6.1"))
    REQ.append(_rt("MTG-BYGGEMØTE","Byggemøter","mandatory","boolean","TE innkaller; BH møterett","Referat føres av TE.",src_file,"§6.2"))
    REQ.append(_rt("MTG-PROSJ","Prosjekteringsmøter","mandatory","boolean","TE innkaller; BH møterett","Referat føres av TE.",src_file,"§6.3"))

    # 6) Månedsrapport – innhold og frister (tabell s.9–10)
    REQ.append(_rt("RAPP-FRIST","Rapportering","mandatory","value","fredag etter siste søndag",
                   "Månedsrapport lastes opp/sendes senest fredag etter siste søndag i måneden (via webhotell).",src_file,"§7 + tabell"))
    REQ.append(_rt("RAPP-OVER","Rapportering – overordnet","mandatory","attachment","09-03-M2",
                   "Overordnet status/avviksforklaring iht. mal 09-03-M2.",src_file,"§7 tabell"))
    REQ.append(_rt("RAPP-KVAL","Rapportering – kvalitet","mandatory","attachment","egenkontroll + avvik",
                   "Utført egenkontroll og kvalitetsavvik med trender/tiltak (09-03-M2).",src_file,"§7 tabell"))
    REQ.append(_rt("RAPP-MILJØ","Rapportering – ytre miljø","mandatory","attachment","MOP 16-06-M; avfallsmengder",
                   "Status mot MOP og avfallsmengder (månedlig/kvartalsvis).",src_file,"§7 tabell"))
    REQ.append(_rt("RAPP-SHA","Rapportering – SHA","mandatory","attachment","indikatorer; nettskjema",
                   "SHA-indikatorer (skader, timer, RUH/vernerundeavvik) iht. veiledning; rapporteres månedlig.",src_file,"§7 tabell"))
    REQ.append(_rt("RAPP-SER","Rapportering – seriøsitet","mandatory","attachment","16-04-M1 + nettskjema",
                   "Egenrapportering seriøsitet (hele kjeden) + månedsrapport SHA.",src_file,"§7 tabell"))
    REQ.append(_rt("RAPP-FREMD","Rapportering – fremdrift","mandatory","attachment","fremdriftsplan + milepæler",
                   "Oppdatert fremdriftsplan og milepæler (hver 14. dag i byggemøter + månedlig i rapport).",src_file,"§7 tabell"))
    REQ.append(_rt("RAPP-PROD","Rapportering – produksjon","mandatory","attachment","bemanning + utført + neste periode",
                   "Bemanning/maskiner, arbeid forrige og neste periode, arbeidsgrunnlag.",src_file,"§7 tabell"))
    REQ.append(_rt("RAPP-ØKON","Rapportering – økonomi","mandatory","attachment","07-02-M9 Økonomirapportering",
                   "Økonomirapport: produsert verdi, avvik, fakturert, endringer.",src_file,"§7 tabell"))

    # Supplementary receipts
    for k,v in TERMS.items():
        RC.append({"type":"contract_term","key":k,"value":v,"source_file":src_file})
    return TERMS, REQ, RC
