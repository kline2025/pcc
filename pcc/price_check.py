from __future__ import annotations
import os, zipfile, csv

def _read_csvs(offer_zip: str):
    if not offer_zip:
        return []
    out = []
    with zipfile.ZipFile(offer_zip, "r") as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            name = info.filename
            ext = os.path.splitext(name)[1].lower()
            if ext not in {".csv"}:
                continue
            data = z.read(info).decode("utf-8", errors="ignore")
            out.append((name, data))
    return out

def _parse_csv(text: str):
    rows = []
    rdr = csv.DictReader(text.splitlines())
    headers = [h.strip() for h in rdr.fieldnames or []]
    for r in rdr:
        rows.append({k.strip(): (v.strip() if isinstance(v,str) else v) for k,v in r.items()})
    return headers, rows

def validate_prices(offer_zip: str) -> dict:
    csvs = _read_csvs(offer_zip)
    found = False
    total_rows = 0
    row_errors = 0
    sum_declared = 0.0
    sum_computed = 0.0
    files = []
    for name, data in csvs:
        headers, rows = _parse_csv(data)
        required = {"item","qty","unit_price","total"}
        if not required.issubset({h.lower() for h in headers}):
            continue
        found = True
        files.append(name)
        for r in rows:
            try:
                qty = float(r.get("qty") or r.get("Qty") or 0)
                unit = float(r.get("unit_price") or r.get("Unit_Price") or 0)
                total = float(r.get("total") or r.get("Total") or 0)
            except ValueError:
                row_errors += 1
                continue
            total_rows += 1
            calc = qty * unit
            sum_declared += total
            sum_computed += calc
            if abs(total - calc) > 0.01:
                row_errors += 1
    ok = (found and row_errors == 0 and abs(sum_declared - sum_computed) <= 0.01)
    return {
        "found": found,
        "files": files,
        "rows_checked": total_rows,
        "row_errors": row_errors,
        "declared_sum": round(sum_declared, 2),
        "computed_sum": round(sum_computed, 2),
        "ok": ok
    }
