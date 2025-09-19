import re

def detect(zf):
    found_itt = {'Leie':False,'Eie':False}
    found_price = {'Leie':False,'Eie':False}
    found_contracts = {'Leie':False,'Eie':False}
    for zi in zf.infolist():
        if zi.is_dir(): continue
        name=zi.filename.lower()
        if name.endswith(".txt"):
            t=zf.read(zi.filename).decode("utf-8","ignore")
            if zi.filename.lower()=="itt.txt":
                if re.search(r'\bleieavtale\b',t,re.I): found_itt['Leie']=True
                if re.search(r'\bsalgsavtale\b|\beie\b',t,re.I): found_itt['Eie']=True
        if name.endswith(".csv"):
            if "prisskjema" in name and "leie" in name: found_price['Leie']=True
            if "prisskjema" in name and "eie" in name: found_price['Eie']=True
        base=name
        if "leieavtale" in base or "statsbygg" in base: found_contracts['Leie']=True
        if "meglerstandard" in base: found_contracts['Eie']=True
    rows=[]
    for v in ("Leie","Eie"):
        rows.append({"variant":v,"in_itt":found_itt[v],"in_price":found_price[v],"in_contracts":found_contracts[v]})
    return rows
