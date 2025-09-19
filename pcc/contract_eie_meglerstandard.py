import re

def extract(text):
    terms={}
    receipts=[]
    m=re.search(r'(\d+)\s*bankdager', text, re.I)
    if m:
        terms['eie:takeover_bankdays_after_conditions']=int(m.group(1))
        receipts.append({'type':'contract_term','path':'Eie','key':'takeover_bankdays_after_conditions','value':int(m.group(1))})
    m=re.search(r'(\d+)\s*måneder[^.\n]*etter\s*sign', text, re.I)
    if m:
        terms['eie:takeover_max_months_after_sign']=int(m.group(1))
        receipts.append({'type':'contract_term','path':'Eie','key':'takeover_max_months_after_sign','value':int(m.group(1))})
    m=re.search(r'30\s*000[^0-9]*per\s*(arbeidsdag|kalenderdag|dag)', text, re.I)
    if m:
        terms['eie:delay_ld_nok_per_day']=30000
        unit = 'working_day' if m.group(1).lower().startswith('arbeids') else ('calendar_day' if m.group(1).lower().startswith('kalender') else 'day')
        terms['eie:ld_day_unit']=unit
        receipts.append({'type':'contract_term','path':'Eie','key':'delay_ld_nok_per_day','value':30000})
        receipts.append({'type':'contract_term','path':'Eie','key':'ld_day_unit','value':unit})
    m=re.search(r'pro\s*&?\s*contra|pro\s+og\s+contra', text, re.I)
    if m:
        m2=re.search(r'(\d+)\s*dager[^.\n]*pro\s*&?\s*contra', text, re.I)
        if m2:
            terms['eie:pro_contra_settlement_days']=int(m2.group(1))
            receipts.append({'type':'contract_term','path':'Eie','key':'pro_contra_settlement_days','value':int(m2.group(1))})
    m=re.search(r'(\d+)\s*%\s*av\s*kjøpesum', text, re.I)
    if m:
        terms['eie:condition_damage_threshold_pct']=int(m.group(1))
        receipts.append({'type':'contract_term','path':'Eie','key':'condition_damage_threshold_pct','value':int(m.group(1))})
    m=re.search(r'(\d+)\s*måneder[^.\n]*reklamasjon', text, re.I)
    if m:
        terms['eie:general_claim_limit_months']=int(m.group(1))
        receipts.append({'type':'contract_term','path':'Eie','key':'general_claim_limit_months','value':int(m.group(1))})
    m=re.search(r'(\d+)\s*år[^.\n]*tittel|tittelmangel', text, re.I)
    if m:
        terms['eie:title_warranty_years']=int(m.group(1))
        receipts.append({'type':'contract_term','path':'Eie','key':'title_warranty_years','value':int(m.group(1))})
    return terms, receipts
