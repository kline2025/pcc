import re
def _weights(text):
    out=[]
    for m in re.finditer(r'([A-Za-zÆØÅæøå \-/]+?)\s*[:\-]?\s*([0-9]{1,3})\s*%', text, flags=re.I):
        out.append((m.group(1).strip(), int(m.group(2)), m.group(0)))
    return out
def _env(text):
    rows={}
    if re.search(r'\bMercell\b',text,re.I): rows["channel"]="Mercell"
    m=re.search(r'fil(?:e|)-?navn[^0-9]{0,30}(\d{1,3})\s*tegn',text,re.I)
    if m: rows["filename_limit_chars"]=m.group(1)
    m=re.search(r'\bspråk[^:\n]*[:]\s*(norsk|norwegian)',text,re.I)
    if m: rows["language"]="nb-NO"
    m=re.search(r'(vedståelsesfrist|bid\s*valid)\s*[: ]\s*(\d{1,2})\s*måneder',text,re.I)
    if m: rows["bid_validity_months"]=m.group(2)
    return rows
def diff(base_txt, add_txt):
    diffs=[]
    bw=_weights(base_txt); aw=_weights(add_txt)
    if bw and aw:
        bsum=sum(p for _,p,_ in bw); asum=sum(p for _,p,_ in aw)
        if bsum!=asum:
            diffs.append({"field":"weights_total_pct","before":str(bsum),"after":str(asum),"source_old":"","source_new":""})
    be=_env(base_txt); ae=_env(add_txt)
    keys=set(be.keys())|set(ae.keys())
    for k in keys:
        bv=be.get(k); av=ae.get(k)
        if bv is not None and av is not None and str(bv)!=str(av):
            diffs.append({"field":"env:"+k,"before":str(bv),"after":str(av),"source_old":"","source_new":""})
    return diffs
def scan(zf):
    base=None; adds=[]
    for zi in zf.infolist():
        if zi.is_dir(): continue
        n=zi.filename
        if n.lower()=="itt.txt":
            base=zf.read(n).decode("utf-8","ignore")
        if re.search(r'(tillegg|endring|oppklaring|klarifisering|q&a|qa).*\.txt$', n, flags=re.I):
            adds.append((n, zf.read(n).decode("utf-8","ignore")))
    out=[]
    if base and adds:
        for name,txt in adds:
            for d in diff(base,txt):
                d["source_old"]="ITT.txt"
                d["source_new"]=name
                out.append(d)
    return out
