from __future__ import annotations
import os, zipfile, re

def parse_addenda(tender_zip: str) -> dict:
    items = []
    overrides = {}
    files = set()
    with zipfile.ZipFile(tender_zip, "r") as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            name = info.filename
            name_l = name.lower()
            if not any(k in name_l for k in ["addendum","addenda","q&a","qa"]):
                continue
            text = z.read(info).decode("utf-8", errors="ignore")
            files.add(name)
            for m in re.findall(r"word\s*limit\s*([0-9]+)", text, flags=re.IGNORECASE):
                wl = int(m)
                items.append({"kind":"word_limit","value":wl,"file":name})
                overrides["word_limit"] = wl
            m = re.search(r"weights?\s*:\s*price\s*([0-9]+(?:\.[0-9]+)?)\s*,\s*quality\s*([0-9]+(?:\.[0-9]+)?)", text, flags=re.IGNORECASE)
            if m:
                p = float(m.group(1)); q = float(m.group(2))
                items.append({"kind":"weights","price":p,"quality":q,"file":name})
                overrides["weights"] = {"price":p,"quality":q}
    return {"found": bool(items), "files": sorted(files), "items": items, "overrides": overrides}
