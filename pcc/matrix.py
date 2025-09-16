from __future__ import annotations
import os, csv

def write_matrices(out_dir: str, mapped: list[dict]) -> None:
    mdir = os.path.join(out_dir, "matrix")
    os.makedirs(mdir, exist_ok=True)
    req_cols = ["req_id","priority","doc","doc_sha256","char_start","char_end","text_snippet"]
    comp_cols = ["req_id","state","state_reason"]
    with open(os.path.join(mdir,"requirements.csv"),"w",encoding="utf-8",newline="") as f:
        w = csv.DictWriter(f, fieldnames=req_cols)
        w.writeheader()
        for r in mapped:
            w.writerow({k:r.get(k,"") for k in req_cols})
    with open(os.path.join(mdir,"compliance.csv"),"w",encoding="utf-8",newline="") as f:
        w = csv.DictWriter(f, fieldnames=comp_cols)
        w.writeheader()
        for r in mapped:
            w.writerow({k:r.get(k,"") for k in comp_cols})
