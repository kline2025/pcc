import re

def extract_constants(text):
    const={}
    receipts=[]
    m=re.search(r'(kpi|konsumprisindeks)[^0-9]{0,20}(\d{1,2}[,\.]\d{1,2})\s*%', text, re.I)
    if m:
        v=m.group(2).replace(',','.')
        const['kpi_pct']=float(v)
        receipts.append({'type':'nv_constant','key':'kpi_pct','value':float(v),'snippet':m.group(0)})
    m=re.search(r'(diskonteringsrente|avkastningskrav)[^0-9]{0,20}(\d{1,2}[,\.]\d{1,2})\s*%', text, re.I)
    if m:
        v=m.group(2).replace(',','.')
        const['discount_rate_pct']=float(v)
        receipts.append({'type':'nv_constant','key':'discount_rate_pct','value':float(v),'snippet':m.group(0)})
    m=re.search(r'(leieperiode|avtaleperiode)[^0-9]{0,20}(\d{1,2})\s*år', text, re.I)
    if m:
        const['term_years']=int(m.group(2))
        receipts.append({'type':'nv_constant','key':'term_years','value':int(m.group(2)),'snippet':m.group(0)})
    m=re.search(r'(oppstart|start)\s*[: ]\s*(\d{4})', text, re.I)
    if m:
        const['start_year']=int(m.group(2))
        receipts.append({'type':'nv_constant','key':'start_year','value':int(m.group(2)),'snippet':m.group(0)})
    m=re.search(r'(kvartal|quarter)\s*[: ]\s*(\d)', text, re.I)
    if m:
        const['start_quarter']=int(m.group(2))
        receipts.append({'type':'nv_constant','key':'start_quarter','value':int(m.group(2)),'snippet':m.group(0)})
    m=re.search(r'(beslutningsdato|decision date)\s*[: ]\s*([0-3]?\d[./-][01]?\d[./-]\d{2,4})', text, re.I)
    if m:
        const['decision_date']=m.group(2)
        receipts.append({'type':'nv_constant','key':'decision_date','value':m.group(2),'snippet':m.group(0)})
    return const, receipts
