import re
def _row(item,value,snippet):
    return {"type":"submission","item":item,"value":value,"source_file":"ITT.txt","source_snippet":snippet}

def extract(text, asset_id):
    rows=[]
    checks=[]
    t=text

    # Channel
    if re.search(r'\bMercell\b',t,re.I):
        rows.append(_row("channel","Mercell","Mercell"))

    # Filename length (e.g., 40 characters)
    m=re.search(r'fil(?:e|)-?navn[^0-9]{0,30}(\d{1,3})\s*tegn',t,re.I)
    if m: rows.append(_row("filename_limit_chars",int(m.group(1)),m.group(0)))

    # Language
    m=re.search(r'\bspråk[^:\n]*[:]\s*(norsk|norwegian)',t,re.I)
    if m: rows.append(_row("language","nb-NO",m.group(0)))

    # Bid validity months
    m=re.search(r'(vedståelsesfrist|bid\s*valid)\s*[: ]\s*(\d{1,2})\s*måneder',t,re.I)
    if m: rows.append(_row("bid_validity_months",int(m.group(2)),m.group(0)))

    # Alternative/parallel offers disallowed (match "ikke <verb>" or "<verb> ikke")
    if re.search(r'(alternativ\w*(?:\s+\w+){0,3}\s+tilbud|parallelle\s+tilbud)',t,re.I):
        if re.search(r'(ikke\s*(mottas|tillates|aksepteres)|(mottas|tillates|aksepteres)\s*ikke)',t,re.I):
            rows.append(_row("alt_offers_allowed",False,"alternativ/parallelle tilbud aksepteres ikke"))

    # Forms
    if re.search(r'\bESPD\b',t,re.I):
        rows.append({"type":"forms","item":"espd_required","value":True,"source_file":"ITT.txt","source_snippet":"ESPD"})
    if re.search(r'\begenerklæring\b.*russisk|sanction|sanksjon',t,re.I):
        rows.append({"type":"forms","item":"sanctions_declaration_required","value":True,"source_file":"ITT.txt","source_snippet":"Egenerklæring om russisk involvering"})

    # Award weights
    weights=[]
    for m in re.finditer(r'([A-Za-zÆØÅæøå \-/]+?)\s*[:\-]?\s*([0-9]{1,3})\s*%', t, flags=re.I):
        name=m.group(1).strip()
        pct=int(m.group(2))
        if name:
            weights.append((name,pct,m.group(0)))
            rows.append({"type":"award_weight","asset_id":asset_id,"criterion":name,"pct":pct,"snippet":m.group(0)})
    total=sum(p for _,p,_ in weights)
    if weights:
        rows.append({"type":"award_weights_total","asset_id":asset_id,"total_pct":total})
        checks.append(("tender:criteria:weights_disclosed", 99<=total<=101, f"total={total}; items={len(weights)}"))

    # Price formula presence (robust: any tender text snippet)
    formula=False
    if re.search(r'(laveste\s*(total)?\s*(pris|kostnad)|lowest\s*(total\s*)?(price|cost))',t,re.I) \
       and re.search(r'(poeng|points|score)',t,re.I) \
       and re.search(r'(propor|proporsjonalt|proportional)',t,re.I):
        formula=True
    if formula:
        rows.append({"type":"price_formula","asset_id":asset_id,"pattern":"proportional_lowest_max=10"})
        checks.append(("tender:criteria:formula_disclosed", True, "pattern=proportional"))

    # Coherence hooks (procedure/lots) if stated
    proc=re.search(r'prosedyre\s*[:]\s*([^\n\r]+)',t,re.I)
    if proc:
        rows.append({"type":"coherence","asset_id":asset_id,"key":"procedure","value":proc.group(1).strip()})
    lots=re.search(r'(delkontrakter|lots?)\s*[:]\s*([^\n\r]+)',t,re.I)
    if lots:
        rows.append({"type":"coherence","asset_id":asset_id,"key":"lots","value":lots.group(2).strip()})

    return rows, checks
