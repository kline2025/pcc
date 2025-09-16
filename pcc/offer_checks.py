from __future__ import annotations
import os, zipfile, re

def _read_texts(zip_path: str):
    texts = []
    if not zip_path:
        return texts
    with zipfile.ZipFile(zip_path, "r") as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            name = info.filename
            ext = os.path.splitext(name)[1].lower()
            if ext not in {".txt", ".csv"}:
                continue
            txt = z.read(info).decode("utf-8", errors="ignore")
            texts.append((name, txt))
    return texts

_PROHIBITED_PATTERNS = [
    r"\bsubject to\b",
    r"\bwe reserve the right\b",
    r"\bunless otherwise agreed\b",
    r"\bno liability\b",
    r"\bpenalties? (?:are )?excluded\b",
    r"\bprice(?:s)? subject to change\b",
    r"\bterms and conditions apply\b",
    r"\bfor guidance only\b",
    r"\bbest efforts? only\b"
]

def detect_prohibited_conditions(offer_zip: str) -> dict:
    hits = []
    files = set()
    for name, txt in _read_texts(offer_zip):
        for pat in _PROHIBITED_PATTERNS:
            for line in txt.splitlines():
                if re.search(pat, line, flags=re.IGNORECASE):
                    hits.append(line.strip())
                    files.add(name)
    return {"found": bool(hits), "files": sorted(files), "sample_lines": hits[:3], "count": len(hits)}

def find_word_limit_in_tender(tender_zip: str) -> int | None:
    limit = None
    with zipfile.ZipFile(tender_zip, "r") as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            name = info.filename
            ext = os.path.splitext(name)[1].lower()
            if ext not in {".txt", ".csv"}:
                continue
            txt = z.read(info).decode("utf-8", errors="ignore")
            m = re.search(r"word\s*limit\s*([0-9]+)", txt, flags=re.IGNORECASE)
            if m:
                limit = int(m.group(1))
    return limit

def offer_word_count(offer_zip: str) -> int:
    total = 0
    for _, txt in _read_texts(offer_zip):
        total += len([w for w in re.findall(r"\b\w+\b", txt)])
    return total

def check_format_ok(tender_zip: str, offer_zip: str, limit_override: int | None = None) -> dict:
    limit = limit_override if limit_override is not None else find_word_limit_in_tender(tender_zip)
    if not offer_zip:
        return {"found_limit": limit is not None, "limit": limit, "offer_words": 0, "ok": False, "reason": "NO_OFFER"}
    words = offer_word_count(offer_zip)
    if limit is None:
        return {"found_limit": False, "limit": None, "offer_words": words, "ok": True, "reason": "NO_LIMIT_FOUND"}
    return {"found_limit": True, "limit": limit, "offer_words": words, "ok": words <= limit, "reason": "OK" if words <= limit else "OVER_LIMIT"}
