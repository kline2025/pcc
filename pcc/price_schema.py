import csv, io, re
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
        lines=data.splitlines()
        rdr=csv.reader(io.StringIO(data))
        try:
            header=next(rdr)
        except StopIteration:
            header=[]
        constants={}
        if re.search(r'levetid|bruksstid',data,re.I):
            m=re.search(r'(\d{1,3})\s*år',data,re.I)
            if m: constants["lifetime_years"]=int(m.group(1))
        if re.search(r'garanti',data,re.I):
            m=re.search(r'(\d{1,3})\s*år',data,re.I)
            if m: constants["warranty_years"]=int(m.group(1))
        if re.search(r'antatt\s*forbruk\s*per\s*år',data,re.I):
            m=re.search(r'antatt\s*forbruk\s*per\s*år[^0-9]{0,20}(\d{1,6})',data,re.I)
            if m: constants["assumed_consumption_per_year"]=int(m.group(1))
        out.append((n, header, constants))
        receipts.append({"type":"price_schema","asset_id":asset_id,"sheet":n,"headers":"|".join(header),"constants":constants})
    return out, receipts
