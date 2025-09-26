#!/usr/bin/env python3
import argparse, csv, os, sys

SECTIONS = [
    ("LD", ["delay_ld:", "stats_ld:", "marketing:penalty"]),
    ("Indexation", ["price:index"]),
    ("Payment", ["payment:"]),
    ("Change caps", ["change:"]),
    ("SLA penalties", ["sla:", "penalty:timebot"]),
    ("DPA/TOMs", ["dpa:", "privacy:", "security:"]),
    ("Logistics/EDI", ["logistics:", "edi:", "invoice:ehf_required"]),
    ("DPS", ["dps:", "calloff:"])
]

def load_terms(path):
    terms = []
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8", newline="") as f:
            r = csv.DictReader(f)
            for row in r:
                terms.append(row)
    return terms

def pick(terms, prefixes):
    out = []
    for t in terms:
        k = t.get("key","")
        if any(k.startswith(p) for p in prefixes):
            out.append(t)
    return out

def md_escape(s):
    return s.replace("|","\\|")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--format", choices=["md","pdf"], default="md")
    args = ap.parse_args()

    ct_path = os.path.join(args.matrix, "contract_terms.csv")
    terms = load_terms(ct_path)
    if not terms:
        print("no contract_terms.csv", file=sys.stderr)
        return 2

    lines = []
    lines.append(f"# Risk card\n")
    for title, prefixes in SECTIONS:
        seg = pick(terms, prefixes)
        if not seg:
            continue
        lines.append(f"## {title}\n")
        for t in seg:
            k = t.get("key","")
            v = t.get("value","")
            unit = t.get("unit","")
            src = t.get("source_file","")
            snip = t.get("source_snippet","")
            val = f"{v}{(' ' + unit) if unit else ''}".strip()
            lines.append(f"- **{md_escape(k)}**: {md_escape(val)}  ⟂ {md_escape(src)}: \"{md_escape(snip[:120])}\"")
        lines.append("")

    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines))

    if args.format == "pdf":
        print("md output written; convert to pdf with your preferred tool", file=sys.stderr)
        return 0

    print(args.out)
    return 0

if __name__ == "__main__":
    sys.exit(main())
