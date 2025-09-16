from __future__ import annotations
import os, zipfile, hashlib, re

MANDATORY_MARKERS = [r"\bMUST\b", r"\bSHALL\b", r"\bREQUIRED\b", r"\bSKAL\b", r"\bMÅ\b"]
STOPWORDS = {
    "the","and","for","with","shall","must","required","provide","provided","signed",
    "include","includes","per","month","pages","word","limit","no","prohibited","caveats",
    "a","an","of","to","in","on","by","or","as","be","is","are","at","from","that","this"
}

def _sha256_hex(b: bytes) -> str:
    import hashlib
    return hashlib.sha256(b).hexdigest()

def _normalize_text(s: str) -> str:
    return s.replace("\r\n","\n").replace("\r","\n")

def _keywords(s: str):
    toks = re.findall(r"[A-Za-zÅÄÖÆØåäöæø]{3,}", s)
    toks = [t.lower() for t in toks if t.lower() not in STOPWORDS]
    seen = []
    for t in toks:
        if t not in seen:
            seen.append(t)
    return seen[:8]

def extract_requirements(tender_zip_path: str):
    reqs = []
    rid = 1
    with zipfile.ZipFile(tender_zip_path, "r") as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            name = info.filename
            ext = os.path.splitext(name)[1].lower()
            if ext not in {".txt",".csv"}:
                continue
            raw = z.read(info)
            sha = _sha256_hex(raw)
            txt = _normalize_text(raw.decode("utf-8", errors="ignore"))
            offset = 0
            for line in txt.split("\n"):
                line_stripped = line.strip()
                if not line_stripped:
                    offset += len(line) + 1
                    continue
                if any(re.search(p, line_stripped, flags=re.IGNORECASE) for p in MANDATORY_MARKERS):
                    reqs.append({
                        "req_id": f"R-{rid:04d}",
                        "priority": "mandatory",
                        "doc": name,
                        "doc_sha256": sha,
                        "char_start": offset,
                        "char_end": offset + len(line),
                        "text_snippet": line_stripped,
                        "keywords": _keywords(line_stripped)
                    })
                    rid += 1
                offset += len(line) + 1
    return reqs

def map_offer(offer_zip_path: str, requirements: list[dict]):
    if not offer_zip_path:
        out = []
        for r in requirements:
            out.append({**r, "state":"review", "state_reason":"NO_OFFER", "offer_anchor": None})
        return out
    all_texts = []
    anchors = {}
    with zipfile.ZipFile(offer_zip_path, "r") as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            name = info.filename
            ext = os.path.splitext(name)[1].lower()
            if ext not in {".txt",".csv"}:
                continue
            raw = z.read(info)
            txt = _normalize_text(raw.decode("utf-8", errors="ignore")).lower()
            all_texts.append(txt)
            anchors[name] = txt
    joined = "\n".join(all_texts)
    out = []
    for r in requirements:
        kw = [k for k in r["keywords"] if len(k) >= 3]
        hits = sum(1 for k in kw if k in joined)
        if hits >= 2:
            state = "present"
            reason = "KW_MATCH>=2"
        elif hits == 1:
            state = "review"
            reason = "KW_MATCH=1"
        else:
            state = "missing"
            reason = "KW_MATCH=0"
        out.append({**r, "state":state, "state_reason":reason, "offer_anchor": None})
    return out
