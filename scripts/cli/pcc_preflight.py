#!/usr/bin/env python3
import argparse, csv, os, sys

def write_csv(path, headers, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        w.writeheader()
        for r in rows:
            w.writerow(r)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    req_path = os.path.join(args.matrix, "requirements_matrix.csv")
    sub_path = os.path.join(args.matrix, "submission_checklist.csv")

    req_rows = []
    if os.path.exists(req_path):
        with open(req_path, "r", encoding="utf-8", newline="") as f:
            r = csv.DictReader(f)
            for row in r:
                req_rows.append({
                    "id": row.get("id",""),
                    "section": row.get("section",""),
                    "kind": row.get("kind",""),
                    "prompt_kind": row.get("prompt_kind",""),
                    "text": row.get("text",""),
                    "value_hint": row.get("value_hint",""),
                    "status": "",
                    "comment": "",
                    "attachment_path": "",
                    "source_file": row.get("source_file","")
                })
    sub_rows = []
    if os.path.exists(sub_path):
        with open(sub_path, "r", encoding="utf-8", newline="") as f:
            r = csv.DictReader(f)
            for row in r:
                sub_rows.append({
                    "doc_code": row.get("doc_code",""),
                    "title": row.get("title",""),
                    "phase": row.get("phase",""),
                    "mandatory": row.get("mandatory",""),
                    "status": "",
                    "comment": ""
                })

    if not req_rows and not sub_rows:
        print("no matrix files found", file=sys.stderr)
        return 2

    base = os.path.splitext(args.out)[0]
    req_out = f"{base}_requirements.csv"
    sub_out = f"{base}_submission.csv"
    write_csv(req_out, ["id","section","kind","prompt_kind","text","value_hint","status","comment","attachment_path","source_file"], req_rows)
    write_csv(sub_out, ["doc_code","title","phase","mandatory","status","comment"], sub_rows)
    print(req_out)
    print(sub_out)
    return 0

if __name__ == "__main__":
    sys.exit(main())
