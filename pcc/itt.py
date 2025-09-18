import re
def _findall_pct(text):
    pairs=[]
    for m in re.finditer(r'([A-Za-zÆØÅæøå \-/]+?)\s*[:\-]?\s*([0-9]{1,3})\s*%', text, flags=re.I):
        name=m.group(1).strip()
        pct=int(m.group(2))
        if name:
            name=re.sub(r'\s+',' ',name)
            pairs.append((name,pct,m.group(0)))
    return pairs
def extract(text, asset_id):
    rows=[]
    checks=[]
    t=text
    if re.search(r'\bMercell\b',t,re.I):
        rows.append({"type":"submission","asset_id":asset_id,"item":"channel","value":"Mercell"})
    m=re.search(r'fil(?:e|)-?navn[^0-9]{0,20}(\d{1,3})\s*tegn',t,re.I)
    if m:
        rows.append({"type":"submission","asset_id":asset_id,"item":"filename_limit_chars","value":int(m.group(1))})
    if re.search(r'\bspråk\b[^\.:\n]*norsk|\bnorwegian\b',t,re.I):
        rows.append({"type":"submission","asset_id":asset_id,"item":"language","value":"nb-NO"})
    if re.search(r'vedståelsesfrist|bid\s*valid',t,re.I):
        m=re.search(r'(\d{1,2})\s*måneder',t,re.I)
        if m: rows.append({"type":"submission","asset_id":asset_id,"item":"bid_validity_months","value":int(m.group(1))})
    if re.search(r'alternativ(e)? tilbud|parallelle tilbud',t,re.I):
        if re.search(r'ikke\s*(mottas|tillates|aksepteres)',t,re.I):
            rows.append({"type":"submission","asset_id":asset_id,"item":"alt_offers_allowed","value":False})
    if re.search(r'\bESPD\b',t,re.I):
        rows.append({"type":"forms","asset_id":asset_id,"item":"espd_required","value":True})
    if re.search(r'\begenerklæring\b.*russisk|sanction|sanksjon',t,re.I):
        rows.append({"type":"forms","asset_id":asset_id,"item":"sanctions_declaration_required","value":True})
    weights=_findall_pct(t)
    total=sum(p for _,p,_ in weights)
    for name,pct,raw in weights:
        rows.append({"type":"award_weight","asset_id":asset_id,"criterion":name,"pct":pct,"snippet":raw})
    if weights:
        rows.append({"type":"award_weights_total","asset_id":asset_id,"total_pct":total})
        checks.append(("tender:criteria:weights_disclosed", total>=99 and total<=101, f"total={total}; items={len(weights)}"))
    formula=False
    if re.search(r'laveste\s*(total)?\s*pris|lowest\s*price',t,re.I) and re.search(r'poeng|points|score',t,re.I) and re.search(r'proport',t,re.I):
        formula=True
    if formula:
        rows.append({"type":"price_formula","asset_id":asset_id,"pattern":"proportional_lowest_max=10"})
        checks.append(("tender:criteria:formula_disclosed", True, "pattern=proportional"))
    return rows, checks
