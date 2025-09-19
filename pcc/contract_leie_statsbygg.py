import re

def extract(text):
    terms={}
    receipts=[]
    if re.search(r'80\s*%[^%\n]*konsumprisindeks|80\s*%[^%\n]*KPI', text, re.I):
        terms['leie:indexation_80pct_cpi']=True
        receipts.append({'type':'contract_term','path':'Leie','key':'indexation_80pct_cpi','value':True})
    if re.search(r'1\s*/\s*365[^a-zA-Z]*dag', text, re.I):
        terms['leie:ld_per_day_fraction']='1/365_annual_rent'
        receipts.append({'type':'contract_term','path':'Leie','key':'ld_per_day_fraction','value':'1/365_annual_rent'})
    m=re.search(r'(\d+)\s*måneder[^.\n]*erstatningsansvar|(\d+)\s*måneds\s*leie[^.\n]*som\s*grense', text, re.I)
    if m:
        val=next(g for g in m.groups() if g)
        terms['leie:damage_cap_months']=int(val)
        receipts.append({'type':'contract_term','path':'Leie','key':'damage_cap_months','value':int(val)})
    if re.search(r'overtakelses[- ]?befaring', text, re.I):
        terms['leie:overtakelses_befaring_required']=True
        receipts.append({'type':'contract_term','path':'Leie','key':'overtakelses_befaring_required','value':True})
    if re.search(r'sikkerhet\s*:\s*ingen|leietaker\s*skal\s*ikke\s*stille\s*sikkerhet', text, re.I):
        terms['leie:tenant_security']='none'
        receipts.append({'type':'contract_term','path':'Leie','key':'tenant_security','value':'none'})
    return terms, receipts
