import re, io, csv, zipfile

def _csv_has_phrase(data, phrases):
    text = data.lower()
    if any(p in text for p in phrases):
        return True
    try:
        rows = list(csv.reader(io.StringIO(data)))
        head = "|".join(rows[0]).lower() if rows else ""
        if any(p in head for p in phrases):
            return True
    except:
        pass
    return False

def _txt_has_phrase(text, phrases):
    t = text.lower()
    return any(p in t for p in phrases)

def detect_from_path(zip_path):
    found_itt = {'Leie':False,'Eie':False}
    found_price = {'Leie':False,'Eie':False}
    found_contracts = {'Leie':False,'Eie':False}
    with zipfile.ZipFile(zip_path,"r") as zf:
        for zi in zf.infolist():
            if zi.is_dir():
                continue
            name = zi.filename.lower()
            data = zf.read(zi.filename).decode("utf-8","ignore")
            if name.endswith("itt.txt"):
                if re.search(r'\bleieavtale\b', data, re.I):
                    found_itt['Leie'] = True
                if re.search(r'\bsalgsavtale\b|\beie\b', data, re.I):
                    found_itt['Eie'] = True
            if name.endswith(".txt"):
                if _txt_has_phrase(data, ["statsbyggs standard leieavtale","leieavtale"]):
                    found_contracts['Leie'] = True
                if _txt_has_phrase(data, ["meglerstandard","salg av eiendom","salgsavtale"]):
                    found_contracts['Eie'] = True
            if name.endswith(".csv"):
                if _csv_has_phrase(data, ["prisskjema leie","leie","grunnleie","felleskost"]):
                    found_price['Leie'] = True
                if _csv_has_phrase(data, ["prisskjema eie","eie","kjøpesum","verdi tomt"]):
                    found_price['Eie'] = True
    rows=[]
    for v in ("Leie","Eie"):
        rows.append({"variant":v,"in_itt":found_itt[v],"in_price":found_price[v],"in_contracts":found_contracts[v]})
    return rows
