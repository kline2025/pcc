import re
from typing import List, Dict, Tuple

def _norm_date(s: str) -> str:
    s = s.strip().replace('.', '-').replace('/', '-')
    parts = s.split('-')
    if len(parts) == 3:
        d, m, y = parts
        if len(y) == 2: y = '20' + y
        return f"{y.zfill(4)}-{m.zfill(2)}-{d.zfill(2)}"
    return s

def _fc(item, value, src_file, snip):
    return {"item": item, "value": value, "source_file": src_file, "source_snippet": snip}

def _nok(s: str) -> int:
    s = s.replace(' ', '').replace('\u00A0','').replace('.', '').replace(',', '')
    m = re.search(r'(\d+)', s)
    return int(m.group(1)) if m else 0

def extract_itt_total(text: str, src_file: str) -> Tuple[List[Dict], List[Dict], List[Dict], List[Dict], List[Dict]]:
    fc=[]; subm=[]; cf=[]; req=[]; rc=[]
    t=text
    if re.search(r'\bmercell',t,re.I): fc.append(_fc("channel","Mercell",src_file,"Mercell"))
    if re.search(r'åpen\s+anbudskonkurranse',t,re.I) and re.search(r'ikke\s+adgang\s+til\s+å\s*forhandle',t,re.I):
        fc.append(_fc("procedure","Åpen anbudskonkurranse (ingen forhandling)",src_file,"åpen anbudskonkurranse"))
    if re.search(r'på\s+norsk|språk[:\s]*norsk',t,re.I): fc.append(_fc("language","nb-NO",src_file,"norsk"))
    m=re.search(r'(bindende|vedståelsesfrist)[^\n\r]{0,40}(\d{1,2})\s*måneder',t,re.I)
    if m: fc.append(_fc("bid_validity_months",int(m.group(2)),src_file,m.group(0)))
    if re.search(r'alternative tilbud\s+aksepteres\s+ikke',t,re.I): fc.append(_fc("alt_offers_allowed",False,src_file,"Alternative tilbud aksepteres ikke"))
    if re.search(r'parallelle tilbud\s+aksepteres\s+ikke',t,re.I): fc.append(_fc("partial_offers_allowed",False,src_file,"ikke adgang til å gi tilbud på deler"))
    if re.search(r'\bespd\b',t,re.I): fc.append(_fc("espd_required",True,src_file,"ESPD"))
    if re.search(r'via\s+Mercell',t,re.I): fc.append(_fc("submission_electronic_only",True,src_file,"via Mercell"))
    if re.search(r'elektronisk\s+signatur',t,re.I): fc.append(_fc("electronic_signature_required",True,src_file,"elektronisk signatur"))
    if re.search(r'ikke\s+inndelt\s+i\s+delkontrakter|ikke\s+delkontrakter',t,re.I): fc.append(_fc("lots","No (ikke delkontrakter)",src_file,"ikke delkontrakter"))
    if re.search(r'sikkerhetsloven|nasjonal\s+sikkerhet',t,re.I): fc.append(_fc("security_law_applicable",True,src_file,"Lov om nasjonal sikkerhet"))
    if re.search(r'taushetserklæring',t,re.I): fc.append(_fc("confidentiality_agreement_required",True,src_file,"Taushetserklæring"))
    dm=re.search(r'fristen[^\n\r]{0,40}([0-3]?\d[./-][01]?\d[./-]\d{2,4}).{0,30}(kl\.*\s*[0-2]?\d[:.]\d{2})',t,re.I)
    if dm: fc.append(_fc("offer_deadline", f"{_norm_date(dm.group(1))} {dm.group(2).replace('.',':').replace('kl','').strip()}", src_file, dm.group(0)))
    im=re.search(r'informasjonsmøte[^\n\r]{0,40}([0-3]?\d[./-][01]?\d[./-]\d{2,4}).{0,30}(kl\.*\s*[0-2]?\d[:.]\d{2})',t,re.I)
    if im: fc.append(_fc("info_meeting_datetime", f"{_norm_date(im.group(1))} {im.group(2).replace('.',':').replace('kl','').strip()}", src_file, im.group(0)))
    sv=re.search(r'befaring[^\n\r]{0,40}([0-3]?\d[./-][01]?\d[./-]\d{2,4}).{0,30}(kl\.*\s*[0-2]?\d[:.]\d{2})',t,re.I)
    if sv: fc.append(_fc("site_visit_datetime", f"{_norm_date(sv.group(1))} {sv.group(2).replace('.',':').replace('kl','').strip()}", src_file, sv.group(0)))
    if re.search(r'gyldig\s+id',t,re.I): fc.append(_fc("site_visit_security","ID (pass/ID-kort/førerkort)",src_file,"gyldig ID"))
    for lab,key in [("Spørsmålsfrist","question_deadline"),("Tildeling","award_notice_planned"),("Kontrakt","contract_sign_planned")]:
        mm=re.search(rf'{lab}\s*([0-3]?\d[./-][01]?\d[./-]\d{{2,4}})',t,re.I)
        if mm: fc.append(_fc(key,_norm_date(mm.group(1)),src_file,mm.group(0)))
    doks=[("IIA2","Totalentreprise tilbudsskjema"),("IIA5","Mal for CV og referanseprosjekter"),
          ("IIA6","Egenerklæring sikkerhet"),("IIA7","Forpliktelseserklæring"),("IIA8","Solidaransvarserklæring"),
          ("IIA9","Egenerklæring sanksjonslovgivning"),("IIA10","Taushetserklæring")]
    for code,title in doks:
        if re.search(code,t,re.I):
            subm.append({"doc_code":code,"title":title,"phase":"Offer","mandatory":True,"source_file":src_file,"snippet":code+" "+title})
    if re.search(r'kvalitet[^%\n]{0,15}50\s*%',t,re.I) and re.search(r'pris[^%\n]{0,15}50\s*%',t,re.I):
        cf.append({"criterion":"Kvalitet – tilbudt personell","weight_pct":50,"group":"quality","total_pct":100,"price_model":"","scoring_model":"0–10 CV/kompetanse","model_anchor":"ITT"})
        cf.append({"criterion":"Pris","weight_pct":50,"group":"price","total_pct":100,"price_model":"linear","scoring_model":"lowest=10; ≥ double → 0","model_anchor":"ITT"})
        rc.append({"type":"award_weights_total","total_pct":100,"source_file":src_file})
    if re.search(r'sideentrepriser',t,re.I) and re.search(r'4\s*%',t,re.I):
        req.append({"req_id":"ITT-2.1.3-SIDEADM","section":"Sideentrepriser","kind":"mandatory","prompt_kind":"description","value_hint":"4 %","krav_text":"Administrasjon/fremdriftskontroll av nye sideentrepriser; 4 % påslag på deres totale vederlag.","source_file":src_file,"source_row":"2.1.3"})
    if re.search(r'hovedbedrift',t,re.I):
        req.append({"req_id":"ITT-2.3-HOVEDBED","section":"Organisasjon/SHA","kind":"mandatory","prompt_kind":"boolean","value_hint":"","krav_text":"Totalentreprenør som hovedbedrift etter aml. §2-2.","source_file":src_file,"source_row":"2.3"})
    if re.search(r'itb',t,re.I):
        req.append({"req_id":"ITT-2.8-ITB","section":"ITB","kind":"mandatory","prompt_kind":"description","value_hint":"","krav_text":"ITB-ansvarlig og plan for systematisk ferdigstillelse.","source_file":src_file,"source_row":"2.8"})
    return fc, subm, cf, req, rc

def extract_price_form(text: str, src_file: str) -> Tuple[List[Dict], List[Dict]]:
    rows=[]; rc=[]
    if re.search(r'tilbudssammendrag',text,re.I) or re.search(r'rigg\s*&\s*drift',text,re.I):
        rows.append({"sheet":"Tilbudssammendrag","headers":"Post|Tittel|Beløp_NOK","constants":"{}"})
    if re.search(r'regningsarbeider',text,re.I):
        rows.append({"sheet":"Regningsarbeider_Lønn","headers":"Kategori|Beskrivelse|Timepris_NOK","constants":"{}"})
        mb=re.search(r'material.*?basis[^0-9]{0,20}([\d .]+)',text,re.I)
        ub=re.search(r'underentrepren[øo]r.*?basis[^0-9]{0,20}([\d .]+)',text,re.I)
        const={"materials_base_nok": _nok(mb.group(1)) if mb else None, "subcontract_base_nok": _nok(ub.group(1)) if ub else None}
        rows.append({"sheet":"Regningsarbeider_Materialer","headers":"Felt|Verdi","constants":str({"materials_base_nok":const["materials_base_nok"]})})
        rows.append({"sheet":"Regningsarbeider_Underentreprenør","headers":"Felt|Verdi","constants":str({"subcontract_base_nok":const["subcontract_base_nok"]})})
    if re.search(r'enhetspriser',text,re.I) or re.search(r'unit\s*price',text,re.I):
        rows.append({"sheet":"Enhetspriser","headers":"Nr|Beskrivelse|Enhet|Pris_eks_mva|Evalueringsmengde","constants":str({"applies_to_evaluation":True})})
    if re.search(r'opsjon',text,re.I):
        rows.append({"sheet":"Opsjoner","headers":"Opsjon_nr|Beskrivelse|Pris_eks_mva","constants":str({"opsjoner_inngår_i_evaluering":True})})
    if re.search(r'ns\s*8407[^.\n]{0,20}26\.?2',text,re.I):
        rows.append({"sheet":"Indeksregulering","headers":"Felt|Verdi","constants":str({"ns8407_pkt":"26.2"})})
        rc.append({"type":"contract_term","key":"price:index_regulation_model","value":"NS8407 pkt 26.2", "source_file":src_file})
    return rows, rc

def extract_avtale_total(text: str, src_file: str) -> Tuple[Dict, List[Dict], List[Dict]]:
    terms={}; rc=[]; req=[]
    t=text
    if re.search(r'ns\s*8407',t,re.I): terms["contract:model"]="NS8407_totalentreprise"
    if re.search(r'elektronisk\s+faktura|EHF',t,re.I): terms["invoice:electronic_required"]=True
    if re.search(r'digital\s+signatur|signeres\s+digitalt',t,re.I): terms["signature:digital"]=True
    if re.search(r'postmottak@statsbygg\.no',t,re.I): terms["process:notice_address_bh"]="Postmottak@statsbygg.no"
    req.append({"req_id":"AVT-ADMIN-NOTICE","section":"Administrasjon","kind":"mandatory","prompt_kind":"attachment","value_hint":"","krav_text":"Følge avtalens varslingsadresse og EHF-fakturaoppsett.","source_file":src_file,"source_row":"admin"})
    for k,v in terms.items(): rc.append({"type":"contract_term","key":k,"value":v,"source_file":src_file})
    return terms, rc, req

def extract_tebok_total(text: str, src_file: str) -> Tuple[Dict, List[Dict], List[Dict]]:
    terms={}; rc=[]; req=[]
    t=text
    if re.search(r'ns\s*8407[: ]?2011',t,re.I): terms["contract:model"]="NS8407:2011_totalentreprise"
    if re.search(r'prosjekteringsmøter.*14\s*dag',t,re.I): terms["meetings:design_every_days"]=14
    if re.search(r'underentreprenørmøter.*14\s*dag',t,re.I): terms["meetings:subcontractor_every_days"]=14
    if re.search(r'10\s*%\s*av\s*kontraktssummen.*utførelsestiden',t,re.I): terms["security:execution_pct"]=10
    if re.search(r'3\s*%\s*.*reklamasjonstiden',t,re.I): terms["security:warranty_pct"]=3; terms["security:warranty_years"]=3
    if re.search(r'ikke\s*overstiger\s*nok\s*250\s*000',t,re.I): terms["security:threshold_no_security_nok"]=250000
    if re.search(r'innen\s*14\s*dag.*blankett\s*2',t,re.I): terms["insurance:doc_due_days"]=14
    if re.search(r'minst\s*150\s*G',t,re.I): terms["insurance:liability_min_G"]=150
    if re.search(r'ikke\s*flere\s*enn\s*to\s*ledd',t,re.I): terms["subchain:max_levels"]=2
    if re.search(r'startbank',t,re.I): terms["startbank:required"]=True
    if re.search(r'fullmakt.*4\s*år',t,re.I): terms["osa:fullmakt_required"]=True
    if re.search(r'sanksjonsloven',t,re.I): terms["sanctions:compliance_required"]=True
    if re.search(r'14\s*dag.*etterlevelse',t,re.I): terms["sanctions:doc_due_days"]=14
    if re.search(r'tropisk\s+tre',t,re.I): terms["env:ban_tropical_timber"]=True
    if re.search(r'én\s+promille.*hverdag',t,re.I): terms["env:mulkt_env_duties_permille"]=1; terms["env:mulkt_env_duties_min_nok"]=1500
    if re.search(r'bot\s+p[åa]\s*NOK\s*10\s*000',t,re.I): terms["env:mulkt_env_nonrectifiable_nok"]=10000
    if re.search(r'oppad\s*begrenset\s*til\s*NOK\s*150\s*000',t,re.I): terms["env:mulkt_inadequate_waste_cap_nok"]=150000
    if re.search(r'bim-?gjennomføringsplan',t,re.I): terms["bim:execution_plan_required"]=True
    if re.search(r'fdv',t,re.I): terms["fdv:deliverables_required"]=True
    if re.search(r'prøvedrift',t,re.I) and re.search(r'1\s*promille',t,re.I): terms["delay:ld_trial_run_permille"]=1
    if re.search(r'15\s*000\s*per\s*hverd',t,re.I): terms["delay:ld_framdriftsplan_nok_per_day"]=15000
    if re.search(r'unngå\s*kontant',t,re.I): terms["payments:ban_cash"]=True
    if re.search(r'arbeidstid.*07[:\.]00.*19[:\.]00',t,re.I): terms["worktime:option_fixed_window"]="07:00–19:00"
    if re.search(r'lærling.*5\s*%',t,re.I): terms["learning:apprentice_pct"]=5
    if re.search(r'5\s*promille.*overtakelse',t,re.I): terms["learning:sanction_flat_permille_at_overtak"]=5
    if re.search(r'40\s*%.*faglært',t,re.I): terms["workforce:skilled_min_pct"]=40
    for k,v in terms.items(): rc.append({"type":"contract_term","key":k,"value":v,"source_file":src_file})
    req.append({"req_id":"TEB-MØTER-14D","section":"Prosess/Organisering","kind":"mandatory","prompt_kind":"boolean","value_hint":"hver 14. dag","krav_text":"Prosjekteringsmøter og Ue-møter hver 14. dag.","source_file":src_file,"source_row":"§2"})
    req.append({"req_id":"TEB-FORSIKRING-14D","section":"Forsikring","kind":"mandatory","prompt_kind":"attachment","value_hint":"14 dager","krav_text":"Dokumentere tings- og ansvarsforsikring innen 14 dager.","source_file":src_file,"source_row":"§4"})
    req.append({"req_id":"TEB-LEVERANDØRKJEDE-2","section":"Seriøsitet","kind":"mandatory","prompt_kind":"boolean","value_hint":"maks 2 ledd","krav_text":"Maks to ledd i leverandørkjeden.","source_file":src_file,"source_row":"§6"})
    return terms, rc, req
