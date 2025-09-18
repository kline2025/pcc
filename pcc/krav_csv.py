import csv, io, re, hashlib
def _norm(s): return (s or "").strip()
def _prompt_kind(text):
    t=text.lower(); kinds=[]
    if "bekreft" in t: kinds.append("boolean")
    if "oppgi" in t or "opplys" in t: kinds.append("value")
    if "beskriv" in t: kinds.append("description")
    if "legg ved" in t or "vedlegg" in t: kinds.append("attachment")
    return "|".join(sorted(set(kinds))) if kinds else "text"
def _is_req(typ): return typ.replace(" ","").lower().startswith("m")
def _is_eval(typ): return typ.strip().upper() in ("E1","E2","E3")
def _priority(typ): return typ.strip().upper()
def _criterion(val):
    v=(val or "").strip(); l=v.lower()
    if "produkt" in l: return "Produkt"
    if "leverandør" in l or "leverandoer" in l or "leverandortjenester" in l: return "Leverandørtjenester"
    return v
def _value_hint(s):
    m=re.search(r'(\d+)\s*(måneder|måned|år|stk|v|kv)', s.lower())
    if m: return m.group(0)
    m2=re.search(r'230v|110v|24\s*måneder|10\s*år', s.lower())
    if m2: return m2.group(0)
    return ""
def _read_csv_from_zip(zf, name):
    with zf.open(name, "r") as f: data=f.read()
    text=data.decode("utf-8","ignore")
    return text, list(csv.reader(io.StringIO(text))), hashlib.sha256(data).hexdigest()
def extract_from_zip(zf, asset_id):
    req_rows=[]; eval_rows=[]; receipts=[]
    for zi in zf.infolist():
        if zi.is_dir(): continue
        if not zi.filename.lower().endswith(".csv"): continue
        if "krav" not in zi.filename.lower(): continue
        text, rows, sheet_hash = _read_csv_from_zip(zf, zi.filename)
        if not rows: continue
        header=[h.strip() for h in rows[0]]
        cols={h:i for i,h in enumerate(header)}
        needed=["Kravnr.","Krav","Type krav"]
        if not all(k in cols for k in needed): continue
        has_crit="Tildelingskriterium" in cols
        section=""
        for i, r in enumerate(rows[1:], start=2):
            if not any(r): continue
            kravnr=_norm(r[cols["Kravnr."]]) if cols["Kravnr."]<len(r) else ""
            krav=_norm(r[cols["Krav"]]) if cols["Krav"]<len(r) else ""
            typ=_norm(r[cols["Type krav"]]) if cols["Type krav"]<len(r) else ""
            if not krav: continue
            if kravnr=="" and typ=="" and len(krav)>0 and len(krav.split())<8:
                section=krav
                continue
            if _is_req(typ):
                kind="mandatory_info" if typ.replace(" ","").lower().startswith("m(") else "mandatory"
                row={"req_id":kravnr or "","section":section,"kind":kind,"prompt_kind":_prompt_kind(krav),"value_hint":_value_hint(krav),"krav_text":krav,"source_file":zi.filename,"source_sheet":zi.filename,"source_row":i}
                req_rows.append(row)
                receipts.append({"type":"krav_req","asset_id":asset_id,"req_id":kravnr or "","section":section,"kind":kind,"prompt_kind":row["prompt_kind"],"sheet_hash":sheet_hash,"snippet":krav[:120],"file":zi.filename,"row":i})
            elif _is_eval(typ):
                crit=_criterion(r[cols["Tildelingskriterium"]]) if has_crit and cols["Tildelingskriterium"]<len(r) else ""
                row={"eval_id":kravnr or "","section":section,"priority_rank":_priority(typ),"criterion":crit,"prompt_kind":_prompt_kind(krav),"krav_text":krav,"source_file":zi.filename,"source_sheet":zi.filename,"source_row":i}
                eval_rows.append(row)
                receipts.append({"type":"krav_eval","asset_id":asset_id,"eval_id":kravnr or "","section":section,"priority_rank":row["priority_rank"],"criterion":crit,"sheet_hash":sheet_hash,"snippet":krav[:120],"file":zi.filename,"row":i})
    receipts.append({"type":"krav_summary","asset_id":asset_id,"req_count":len(req_rows),"eval_count":len(eval_rows)})
    return req_rows, eval_rows, receipts
