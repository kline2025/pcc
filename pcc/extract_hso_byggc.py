import re
from typing import List, Dict, Tuple, Optional

def _clean(s:str)->str:
    return (s or "").strip()

def _norm_date(d:str)->str:
    s=d.replace('.','-').replace('/','-').strip()
    parts=s.split('-')
    if len(parts)==3:
        d,m,y=parts
        if len(y)==2: y='20'+y
        return f"{y.zfill(4)}-{m.zfill(2)}-{d.zfill(2)}"
    return s

def _fc(item, value, file, snip):
    return {"item":item,"value":value,"source_file":file,"source_snippet":snip}

def extract_itt_text(text:str, src_file:str)->Tuple[List[Dict],List[Dict],List[Dict],List[Dict]]:
    fc=[]; subm=[]; cf=[]; rc=[]
    t=text

    if re.search(r'\bmercell\b',t,re.I): fc.append(_fc("channel","Mercell",src_file,"Mercell"))
    if re.search(r'åpen\s+anbudskonkurranse',t,re.I): fc.append(_fc("procedure","Åpen anbudskonkurranse (FOA del I og III); ingen forhandling",src_file,"åpen anbudskonkurranse"))
    if re.search(r'språk[:\s]*norsk|skrevet på norsk',t,re.I): fc.append(_fc("language","nb-NO",src_file,"norsk"))
    m=re.search(r'filnavn[^.\n]{0,60}40\s*tegn',t,re.I)
    if m: fc.append(_fc("filename_limit_chars",40,src_file,m.group(0)))
    m=re.search(r'(bindende|vedståelsesfrist)[^\n\r]{0,40}(\d{1,2})\s*måneder',t,re.I)
    if m: fc.append(_fc("bid_validity_months",int(m.group(2)),src_file,m.group(0)))
    if re.search(r'alternative tilbud\s+aksepteres\s+ikke',t,re.I): fc.append(_fc("alt_offers_allowed",False,src_file,"Alternative tilbud aksepteres ikke"))
    if re.search(r'parallelle tilbud\s+aksepteres\s+ikke',t,re.I): fc.append(_fc("parallel_offers_allowed",False,src_file,"Parallelle tilbud aksepteres ikke"))
    if re.search(r'\bespd\b',t,re.I): fc.append(_fc("espd_required",True,src_file,"ESPD"))
    if re.search(r'\bebevis\b',t,re.I): fc.append(_fc("ebevis_used",True,src_file,"eBevis"))
    if re.search(r'ikke\s+inndelt\s+i\s+delkontrakter|ikke\s+delkontrakter',t,re.I): fc.append(_fc("lots","No (ikke delkontrakter)",src_file,"ikke delkontrakter"))
    if re.search(r'generalentreprise\s+basert\s+på\s+ns\s*8405:?\s*2008',t,re.I): fc.append(_fc("contract_type","Generalentreprise NS 8405:2008",src_file,"NS8405:2008"))
    m=re.search(r'planlagt\s+oppstart[^\n\r]{0,20}([0-3]?\d[./-][01]?\d[./-]\d{2,4})|oppstart\s+januar\s+(\d{4})',t,re.I)
    if m:
        d=m.group(1) or f"01-01-{m.group(2)}"
        fc.append(_fc("contract_start",_norm_date(d),src_file,m.group(0)))
    m=re.search(r'gjennomføringstid[^\n\r]{0,30}(\d{1,3})\s*uker',t,re.I)
    if m: fc.append(_fc("contract_duration_weeks",int(m.group(1)),src_file,m.group(0)))
    m=re.search(r'estimert verdi[^\n\r]{0,40}([0-9 ]+)\s*millioner',t,re.I)
    if m:
        try: fc.append(_fc("estimated_value_nok_mill",int(m.group(1).replace(' ','')),src_file,m.group(0)))
        except: pass

    m=re.search(r'tilbudsbefaring[^\n\r]{0,40}([0-3]?\d[./-][01]?\d[./-]\d{2,4}).{0,20}kl\s*([0-2]?\d[:.]\d{2})',t,re.I)
    if m: fc.append(_fc("site_visit_datetime",f"{_norm_date(m.group(1))} {m.group(2).replace('.',':')}",src_file,m.group(0)))
    m=re.search(r'maksimalt\s*to\s*representanter',t,re.I)
    if m: fc.append(_fc("site_visit_max_participants_per_bidder",2,src_file,m.group(0)))

    for lab,key in [("Spørsmålsfrist","question_deadline"),("Tilbudsfrist","offer_deadline"),("Tildeling","award_notice_planned"),("Kontrakt","contract_sign_planned")]:
        m=re.search(rf'{lab}\s*([0-3]?\d[./-][01]?\d[./-]\d{{2,4}})',t,re.I)
        if m: fc.append(_fc(key,_norm_date(m.group(1)),src_file,m.group(0)))

    if re.search(r'seriøsitetskrav',t,re.I): fc.append(_fc("seriousness_requirements_doc","D7_Seriositetsbestemmelser",src_file,"seriøsitetskrav"))
    if re.search(r'elvirksomhetsregister',t,re.I): fc.append(_fc("elvirksomhetsregister_required",True,src_file,"Elvirksomhetsregisteret"))

    m=re.search(r'leverandørkjeden[^.\n]{0,40}to\s*ledd',t,re.I)
    if m: fc.append(_fc("supplier_chain_max_levels",2,src_file,m.group(0)))

    DOKs=[("003_Konk_skjema","Konkurranseskjema (Excel)"),
          ("003_Referanseprosjekter","Skjema for referanseprosjekter (mal)"),
          ("003_Tilbudsbrev","Tilbudsbrev"),
          ("004_Forpliktelseserklaering","Forpliktelseserklæring (hvis aktuelt)"),
          ("004_Internasjonale_sanksjoner","Egenerklæring om russisk involvering"),
          ("007_Skjermingsbegrunnelse","Bruksanvisning og begrunnelse for sladding (hvis aktuelt)"),
          ("032_Morselskapsgaranti","Morselskapsgaranti (hvis aktuelt)"),
          ("A3_CV_Anleggsleder","CV for anleggsleder"),
          ("A3_CV_ITB","CV for ITB"),
          ("A3_CV_PL","CV for prosjektleder"),
          ("F1_Prisposter","F.1 Prisposter (utskrift/PDF)"),
          ("F1_Pris_sammendrag","F.1 Prissammenstilling"),
          ("F2_Regningsarbeider","F.2 Regningsarbeider"),
          ("F4_Opsjoner","F.4 Opsjoner")]
    for code,title in DOKs:
        if re.search(code.replace('_','[ _]'),t,re.I):
            subm.append({"doc_code":code,"title":title,"phase":"Offer","mandatory":True,"source_file":src_file,"snippet":code+" "+title})

    weights=[]; tot=None
    if re.search(r'pris[^%\n]{0,15}70\s*%',t,re.I): weights.append(("Pris",70))
    if re.search(r'kvalitet[^%\n]{0,15}30\s*%',t,re.I): weights.append(("Kvalitet (nøkkelpersonell)",30))
    tot=sum(p for _,p in weights) if weights else None
    for name,p in weights:
        cf.append({"criterion":name,"weight_pct":p,"group":"price" if "pris" in name.lower() else "quality",
                   "total_pct":tot or "", "price_model":"konkurranseskjema_lineær" if "Pris"==name else "",
                   "scoring_model":"0–10; laveste=10; dobbel pris=0" if "Pris"==name else "0–10 relativ til beste",
                   "model_anchor":"Konkurranseskjema"})
    if tot is not None: rc.append({"type":"award_weights_total","total_pct":tot,"source_file":src_file})

    return fc,subm,cf,rc

def extract_konkurranseskjema_text(text:str, src_file:str)->Tuple[List[Dict],List[Dict]]:
    price_rows=[]; receipts=[]
    t=text
    if re.search(r'isy/?gprog',t,re.I): receipts.append({"type":"pricing_note","key":"isy_gprog_supported","value":True,"source_file":src_file})
    if re.search(r'prissammenstilling',t,re.I): price_rows.append({"sheet":"F.1_Prissammenstilling","headers":"Kapittel|Kapittelsum|Evalueringspåslag|Kontraktssum ekskl MVA","constants":"{}"})
    if re.search(r'prisposter',t,re.I): price_rows.append({"sheet":"F.1_Prisposter","headers":"Post nummer|Kode|Tittel|Enhet|Mengde|EnhetsPris|Postsum","constants":"{}"})
    if re.search(r'kapittelsum',t,re.I): price_rows.append({"sheet":"F.1_Kapittelsummer","headers":"Radetiketter|Kapittelsum|Ant. Prisposter|Restanser","constants":"{}"})
    if re.search(r'regningsarbeider',t,re.I): price_rows.append({"sheet":"F.2_Regningsarbeider","headers":"Timepriser ekskl MVA|Påslag %|Materialbasis|Andre kostnader","constants":"{}"})
    if re.search(r'opsjoner',t,re.I): price_rows.append({"sheet":"F.4_Opsjoner","headers":"Opsjonsposter|Beskrivelse|Pris NOK eks MVA","constants":"{}"})
    return price_rows, receipts

def extract_avtale_text(text:str, src_file:str)->Tuple[Dict,List[Dict],List[Dict]]:
    terms={}; rc=[]; req=[]
    t=text
    if re.search(r'ns\s*8405:?\s*2008',t,re.I): terms["contract:model"]="NS8405:2008_generalentreprise"
    if re.search(r'ehf',t,re.I): terms["process:invoice_ehf_required"]=True
    m=re.search(r'minimum\s*30\s*dagers\s*forfall',t,re.I)
    if m: terms["payment:days_min"]=30
    if re.search(r'betalingsplan[^\n\r]{0,30}3\s*uker',t,re.I): terms["process:payment_plan_due_weeks"]=3
    if re.search(r'miljøoppfølging|mop',t,re.I): terms["env:mop_required"]=True
    if re.search(r'rent\s*tørt\s*bygg|rtb',t,re.I): terms["clean:rtb_required"]=True
    if re.search(r'bim-?gjennomføringsplan|c44',t,re.I): terms["bim:execution_plan_required"]=True
    if re.search(r'fdv[- ]instruks|c47',t,re.I): terms["fdv:deliverables_required"]=True
    m=re.search(r'overtagelse[^\n\r]{0,40}([0-3]?\d[./-][01]?\d[./-]\d{2,4})',t,re.I)
    if m: terms["handover:takeover_date"]=_norm_date(m.group(1))
    if re.search(r'prøvedrift[^\n\r]{0,20}12\s*mnd',t,re.I): terms["commissioning:trial_run_heating"]=12
    if re.search(r'prøvedrift[^\n\r]{0,20}6\s*mnd',t,re.I): terms["commissioning:trial_run_other"]=6
    if re.search(r'dagmulkten[^\n\r]{0,40}1\s*‰',t,re.I): terms["delay:ld_rate_permil_per_day"]="1"
    req.append({"req_id":"D.3-1","section":"SHA","kind":"mandatory","prompt_kind":"boolean","value_hint":"","krav_text":"Entreprenør er Hovedbedrift; følge SHA-plan/ID-kort/oversiktslister.","source_file":src_file,"source_row":"D.3"})
    req.append({"req_id":"D.5-1","section":"Miljø","kind":"mandatory","prompt_kind":"attachment","value_hint":"","krav_text":"Miljøoppfølgingsplan (MOP) – leveres.","source_file":src_file,"source_row":"D.5"})
    req.append({"req_id":"D.6-1","section":"RTB","kind":"mandatory","prompt_kind":"attachment","value_hint":"","krav_text":"Rent Tørt Bygg – følges.","source_file":src_file,"source_row":"D.6"})
    return terms, rc, req

def extract_endringsbest_text(text:str, src_file:str)->Tuple[Dict,List[Dict]]:
    t=text; terms={}; rc=[]
    m=re.search(r'netto\s*endringsarbeider[^\n\r]{0,40}(\d{1,2})\s*%',t,re.I)
    if m: terms["change:max_net_addition_pct"]=int(m.group(1))
    if re.search(r'varsle[^\n\r]{0,30}før\s*endringsarbeidet',t,re.I): terms["change:irregular_order_notice_required"]=True
    if re.search(r'forsering',t,re.I): terms["change:forsering_allowed_by_order"]=True
    if re.search(r'fristforlengelse[^\n\r]{0,30}(\d{1,2})\s*%',t,re.I): terms["extension:fristforlengelse_threshold_change_pct"]=int(re.search(r'(\d{1,2})\s*%',m.group(0)).group(1)) if m else None
    if re.search(r'ns\s*3405|08655',t,re.I): terms["price:index_regulation"]="NS3405_totalindeks_Bustadblokk_08655"; terms["price:index_base"]="offer_month"
    if re.search(r'trekkes\s*10\s*%',t,re.I): terms["payment:progress_retention_pct"]=10
    if re.search(r'to\s*måneder\s+fra\s+mottakelsen\s+av\s+sluttoppstillingen',t,re.I): terms["payment:final_invoice_due_months"]=2
    if re.search(r'1\s*‰\s*av\s*kontraktssum',t,re.I): terms["delay:ld_rate_permille_per_workday"]="1"
    if re.search(r'minst\s*kr\s*1\s*500',t,re.I): terms["delay:ld_min_main_nok_per_day"]=1500
    if re.search(r'minst\s*kr\s*750',t,re.I): terms["delay:ld_min_milestone_nok_per_day"]=750
    if re.search(r'begrenset\s*til\s*10\s*%',t,re.I): terms["delay:ld_cap_pct_of_contract"]=10
    if re.search(r'150\s*G',t,re.I): terms["insurance:liability_min_G"]=150
    if re.search(r'ikke\s*flere\s*enn\s*to\s*ledd',t,re.I): terms["site:two_tier_subchain_limit"]=True
    if re.search(r'oppmann',t,re.I): terms["disputes:oppmann_option"]=True
    if re.search(r'100\s*G[^.\n]*rettergang',t,re.I): terms["disputes:court_threshold_G"]=100
    if re.search(r'100\s*G[^.\n]*voldgift',t,re.I): terms["disputes:arbitration_threshold_G"]=100
    return terms, rc

def extract_c21_text(text:str, src_file:str)->Tuple[List[Dict],List[Dict]]:
    rows=[]; rc=[]
    add=lambda r: rows.append(r)
    def R(id,sec,kind,pk,hint,txt,row):
        add({"req_id":id,"section":sec,"kind":kind,"prompt_kind":pk,"value_hint":hint,"krav_text":txt,"source_file":src_file,"source_row":row})

    if re.search(r'ns\s*3420\s*del\s*a',text,re.I):
        R("01.0-GEN","Rigg & drift (NS3420 A)","mandatory","description","","Rigg og driftsytelser iht. NS3420 del A.", "01-1")
    R("01.0-HOVEDBEDRIFT","SHA","mandatory","boolean","","Entreprenør er hovedbedrift iht. BHF.","01-1")
    R("01.0-FDV-SOMBYGGET","FDV/Sluttdok","mandatory","attachment","","Som-bygget/FDV iht. C47.","01-1")
    R("01.0-TFM-MERKING","Merking/Tekniske systemer","mandatory","boolean","","TFM-merking (3-sifret) iht. NS 3451/TFM.","01-1")
    R("01.1-SYSFERD","Systematisk ferdigstillelse","mandatory","attachment","","Systematisk ferdigstillelse; ITB etter NS3935/NS6450; SDC i drift før overlevering.","01-2")
    R("01.7-RTB","Rent Tørt Bygg","mandatory","boolean","", "RTB-krav følges; rund sum.", "01-5")
    R("01.9.1-AVFALL","Avfall","mandatory","value","≥90 %","Minst 90 % avfall sorteres til godkjent mottak.", "01-5")
    R("01.24-ITB-ANSVAR","ITB","mandatory","attachment","","ITB-arbeider iht. vedlegg; tverrfaglige tester.", "01-15")
    R("01.26-SI-TIME","ITB/Systemintegrator","mandatory","value","350 t","Rolle Systemintegrator iht. NS3935/NS6450.","01-16")
    R("01.32-PRØVEDRIFT","Prøvedrift","mandatory","value","150 t","Administrasjon prøvedrift iht. kontrakt/plan.","01-20")
    return rows, rc
