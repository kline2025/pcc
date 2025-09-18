import csv, io, re
def _norm(s):
    return (s or "").strip()
def _prompt_kind(text):
    t = text.lower()
    kinds = []
    if "bekreft" in t: kinds.append("boolean")
    if "oppgi" in t or "opplys" in t: kinds.append("value")
    if "beskriv" in t: kinds.append("description")
    if "legg ved" in t or "vedlegg" in t: kinds.append("attachment")
    if not kinds: return "text"
    return "|".join(sorted(set(kinds)))
def _is_req(typ):
    t = typ.replace(" ", "").lower()
    return t.startswith("m")
def _is_eval(typ):
    t = typ.strip().upper()
    return t in ("E1","E2","E3")
def _priority(typ):
    return typ.strip().upper()
def _criterion(val):
    v = (val or "").strip()
    if not v: return ""
    l = v.lower()
    if "produkt" in l: return "Produkt"
    if "leverandør" in l or "leverandoer" in l or "leverandortjenester" in l: return "Leverandørtjenester"
    return v
def _read_csv_from_zip(zf, name):
    with zf.open(name, "r") as f:
        data = f.read()
    text = data.decode("utf-8", "ignore")
    return list(csv.reader(io.StringIO(text)))
def extract_from_zip(zf, asset_id):
    req_rows = []
    eval_rows = []
    receipts = []
    for zi in zf.infolist():
        if zi.is_dir(): continue
        if not zi.filename.lower().endswith(".csv"): continue
        if "krav" not in zi.filename.lower(): continue
        rows = _read_csv_from_zip(zf, zi.filename)
        if not rows: continue
        header = [h.strip() for h in rows[0]]
        cols = {h:i for i,h in enumerate(header)}
        needed = ["Kravnr.","Krav","Type krav"]
        if not all(k in cols for k in needed):
            continue
        has_crit = "Tildelingskriterium" in cols
        for i, r in enumerate(rows[1:], start=2):
            if not any(r): continue
            kravnr = _norm(r[cols["Kravnr."]]) if cols["Kravnr."] < len(r) else ""
            krav = _norm(r[cols["Krav"]]) if cols["Krav"] < len(r) else ""
            typ = _norm(r[cols["Type krav"]]) if cols["Type krav"] < len(r) else ""
            if not krav: continue
            if _is_req(typ):
                kind = "mandatory_info" if typ.replace(" ","").lower().startswith("m(") else "mandatory"
                req_rows.append({
                    "req_id": kravnr or "",
                    "kind": kind,
                    "prompt_kind": _prompt_kind(krav),
                    "krav_text": krav,
                    "source_file": zi.filename,
                    "source_row": i
                })
                receipts.append({
                    "type":"krav_req",
                    "asset_id": asset_id,
                    "req_id": kravnr or "",
                    "kind": kind,
                    "prompt_kind": _prompt_kind(krav),
                    "snippet": krav[:120],
                    "file": zi.filename,
                    "row": i
                })
            elif _is_eval(typ):
                crit = _criterion(r[cols["Tildelingskriterium"]]) if has_crit and cols["Tildelingskriterium"] < len(r) else ""
                eval_rows.append({
                    "eval_id": kravnr or "",
                    "priority_rank": _priority(typ),
                    "criterion": crit,
                    "prompt_kind": _prompt_kind(krav),
                    "krav_text": krav,
                    "source_file": zi.filename,
                    "source_row": i
                })
                receipts.append({
                    "type":"krav_eval",
                    "asset_id": asset_id,
                    "eval_id": kravnr or "",
                    "priority_rank": _priority(typ),
                    "criterion": crit,
                    "snippet": krav[:120],
                    "file": zi.filename,
                    "row": i
                })
    receipts.append({"type":"krav_summary","asset_id":asset_id,"req_count":len(req_rows),"eval_count":len(eval_rows)})
    return req_rows, eval_rows, receipts
