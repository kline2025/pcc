import csv, io, re, hashlib
def _read_csv_from_zip(zf, name):
    with zf.open(name, "r") as f:
        data=f.read().decode("utf-8","ignore")
    return data
def extract(zf, asset_id):
    out=[]
    receipts=[]
    for zi in zf.infolist():
        if zi.is_dir(): continue
        n=zi.filename
        ln=n.lower()
        if not ln.endswith(".csv"): continue
        if "prisskjema" not in ln: continue
        data=_read_csv_from_zip(zf,n)
        text=data
        rdr=csv.reader(io.StringIO(data))
        try:
            header=next(rdr)
        except StopIteration:
            header=[]
        constants={}
        m=re.search(r'levetid|bruksstid',text,re.I)
        if m:
            m2=re.search(r'(?:levetid|bruksstid)[^0-9]{0,20}(\d{1,3})\s*år',text,re.I)
            if m2: constants["lifetime_years"]=int(m2.group(1))
        m=re.search(r'garanti',text,re.I)
        if m:
            m2=re.search(r'(?:garanti|garantitid)[^0-9]{0,20}(\d{1,3})\s*år',text,re.I)
            if m2: constants["warranty_years"]=int(m2.group(1))
        m=re.search(r'antatt\s*forbruk\s*per\s*år[^0-9]{0,20}(\d{1,6})',text,re.I)
        if m: constants["assumed_consumption_per_year"]=int(m.group(1))
        if re.search(r'Totalsum\s*forbruksmateriell',text,re.I):
            receipts.append({"type":"price_totals_row_present","asset_id":asset_id,"sheet":n})
        for sl in ("Servicenivå 0","Servicenivå 1","Servicenivå 2"):
            if sl.lower() in text.lower():
                receipts.append({"type":"service_level_priceline_present","asset_id":asset_id,"sheet":n,"level":sl})
        out.append((n, header, constants))
        receipts.append({"type":"price_schema","asset_id":asset_id,"sheet":n,"headers":"|".join(header),"constants":constants})
    return out, receipts
