import re
def detect_formula_in_text(text):
    r1=r'(laveste\s*(total)?\s*(pris|kostnad)|lowest\s*(total\s*)?(price|cost))'
    r2=r'(poeng|score|points)'
    r3=r'(proporsjon|propor|proportional|forholdsmessig)'
    win=150
    for line in text.splitlines():
        s=line.strip()
        if re.search(r1,s,re.I) and re.search(r2,s,re.I) and re.search(r3,s,re.I):
            return True,s
    text2=re.sub(r'\s+',' ',text)
    for m in re.finditer(r'.{1,%d}'%win,text2,re.S):
        s=m.group(0)
        if re.search(r1,s,re.I) and re.search(r2,s,re.I) and re.search(r3,s,re.I):
            return True,s.strip()
    return False,""
def scan_zip_for_formula(zf, asset_id):
    receipts=[]
    found=False
    snippet=""
    src_file=""
    for zi in zf.infolist():
        if zi.is_dir(): continue
        if not zi.filename.lower().endswith(".txt"): continue
        t=zf.read(zi.filename).decode("utf-8","ignore")
        ok,snip=detect_formula_in_text(t)
        if ok:
            found=True
            snippet=snip
            src_file=zi.filename
            break
    if found:
        receipts.append({"type":"price_formula","asset_id":asset_id,"pattern":"proportional_lowest_max=10","source_file":src_file,"source_snippet":snippet})
    return found, receipts
