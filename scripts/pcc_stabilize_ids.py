#!/usr/bin/env python3
import argparse, csv, hashlib, os, sys

def short_id(s):
    h = hashlib.sha256(s.encode('utf-8')).hexdigest()
    return "REQ-" + h[:8]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", dest="outp", required=True)
    args = ap.parse_args()

    rows = []
    with open(args.inp, "r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        fieldnames = r.fieldnames
        for row in r:
            rows.append(row)

    out_fields = ['id','section','kind','prompt_kind','text','value_hint','source_file','source_snippet']
    with open(args.outp, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=out_fields)
        w.writeheader()
        seen = {}
        for row in rows:
            section = row.get('section','').strip()
            pk = row.get('prompt_kind','').strip()
            text = row.get('text','').strip()
            src = row.get('source_file','').strip()
            snip = row.get('source_snippet','').strip()
            base = f"{section}|{pk}|{text}|{src}|{snip[:64]}"
            rid = short_id(base)
            if rid in seen:
                i = 1
                while f"{rid}-{i}" in seen:
                    i += 1
                rid = f"{rid}-{i}"
            seen[rid] = True
            out = {
                'id': rid,
                'section': section,
                'kind': row.get('kind','').strip(),
                'prompt_kind': pk,
                'text': text,
                'value_hint': row.get('value_hint','').strip(),
                'source_file': src,
                'source_snippet': snip
            }
            w.writerow(out)

if __name__ == "__main__":
    sys.exit(main())
