import re

def extract_from_itt(text):
    rows=[]
    receipts=[]
    total=None
    weights=[]
    for m in re.finditer(r'([A-Za-zÆØÅæøå/() \-]+?)\s*[:\-]?\s*([0-9]{1,3})\s*%', text, flags=re.I):
        name=m.group(1).strip()
        pct=int(m.group(2))
        weights.append((name,pct,m.group(0)))
    if weights:
        total=sum(p for _,p,_ in weights)
        for name,pct,snip in weights:
            rows.append({'criterion':name,'weight_pct':pct,'group':'','total_pct':total,'price_model':'','scoring_model':'','model_anchor':''})
        receipts.append({'type':'award_weights_total','total_pct':total,'snippet':weights[0][2]})
    model_present=False
    if re.search(r'(nåverdi|npv)', text, re.I) and re.search(r'(prisskjema|underlag)', text, re.I):
        model_present=True
    scoring=None
    if re.search(r'lineær', text, re.I) or re.search(r'linear', text, re.I):
        scoring='lineær'
    return rows, total, model_present, scoring, receipts
