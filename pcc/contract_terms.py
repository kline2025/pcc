import re
def _find_num(pattern, text, cast=float):
    m = re.search(pattern, text, flags=re.I)
    if not m: return None
    g = [x for x in m.groups() if x is not None]
    if not g: return None
    try:
        val = g[0].replace(" ","").replace(",",".")
        return cast(val)
    except: return None
def extract(text, asset_id):
    t=text
    terms={}
    receipts=[]
    if re.search(r'\bDDP\b.*Incoterms\s*[^0-9]*2020', t, flags=re.I):
        terms["delivery_incoterms"]="DDP_Incoterms2020"
    v=_find_num(r'0[,\.]?25\s*%\s', t);     terms.update({"delay_ld_rate_pct_per_working_day":v} if v is not None else {})
    v=_find_num(r'\bkr?\s*200\b', t, cast=float);     terms.update({"delay_ld_min_nok_per_day":v} if v is not None else {})
    v=_find_num(r'begrenset\s*til\s*(\d+)\s*virkedager', t, cast=int);     terms.update({"delay_ld_max_working_days":v} if v is not None else {})
    v=_find_num(r'NOK\s*(500)\s*pr\s*arbeidsdag', t, cast=float);     terms.update({"catalog_ld_nok_per_working_day":v} if v is not None else {})
    v=_find_num(r'Betalingsfrist\s*er\s*(\d+)\s*dager', t, cast=int);     terms.update({"payment_days":v} if v is not None else {})
    if re.search(r'konsumprisindeks|KPI', t, flags=re.I): terms["indexation_index"]="KPI"
    v=_find_num(r'Prisene\s*er\s*faste\s*i\s*(\d+)\s*måneder', t, cast=int);     terms.update({"indexation_first_fixed_months":v} if v is not None else {})
    v=_find_num(r'minimum\s*(\d+)\s*uker', t, cast=int);     terms.update({"indexation_notice_weeks":v} if v is not None else {})
    v=_find_num(r'justeres\s*fra\s*og\s*med\s*(\d+)\s*måneder\s*etter', t, cast=int);     terms.update({"indexation_late_effect_months":v} if v is not None else {})
    if re.search(r'Prisene\s*justeres\s*ikke\s*som\s*følge\s*av\s*valuta', t, flags=re.I): terms["fx_adjustments_allowed"]=False
    v=_find_num(r'netto\s*utgjør\s*mer\s*enn\s*(\d+)\s*%', t, cast=float);     terms.update({"authority_change_threshold_pct":v} if v is not None else {})
    v=_find_num(r'De\s*første\s*(\d+)\s*måneder\s*av\s*Avtaleperioden\s*er\s*prøvetid', t, cast=int);     terms.update({"probation_months":v} if v is not None else {})
    v=_find_num(r'si\s*opp\s*Avtalen\s*med\s*(\d+)\s*dagers\s*varsel', t, cast=int);     terms.update({"probation_termination_notice_days":v} if v is not None else {})
    v=_find_num(r'med\s*(\d+)\s*måneders\s*varsel', t, cast=int);     terms.update({"termination_notice_months":v} if v is not None else {})
    v=_find_num(r'varer\s*lenger\s*enn\s*(\d+)\s*kalenderdager', t, cast=int);     terms.update({"force_majeure_termination_days":v} if v is not None else {})
    v=_find_num(r'med\s*(\d+)\s*kalenderdagers\s*varsel', t, cast=int);     terms.update({"force_majeure_notice_days":v} if v is not None else {})
    if re.search(r'returner[e]? ubrukte varer|return unused goods|ubrukte varer kan returneres', t, flags=re.I): terms["return_policy_unused_allowed"]=True
    v=_find_num(r'bot\s*på\s*(0[,\.]2)\s*%\s*av\s*kontraktens\s*samlede\s*verdi', t);     terms.update({"marketing_penalty_pct":float(v)} if v is not None else {})
    v=_find_num(r'eller\s*(10[ \u00A0]?000)\s*kroner', t, cast=float);     terms.update({"marketing_penalty_min_nok":v} if v is not None else {})
    for k,v in terms.items(): receipts.append({"type":"contract_term","asset_id":asset_id,"key":k,"value":v})
    receipts.append({"type":"contract_terms","asset_id":asset_id,"keys":len(terms)})
    return terms, receipts
