#!/usr/bin/env python3
import argparse, csv, os, re, sys, json
from collections import defaultdict

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--matrix", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()

    crit_path = os.path.join(args.matrix, "criteria_and_formula.csv")
    ps_path = os.path.join(args.matrix, "price_schema.csv")

    if not os.path.exists(crit_path):
        print("criteria_and_formula.csv missing", file=sys.stderr)
        return 2

    lots = defaultdict(list)
    with open(crit_path, "r", encoding="utf-8", newline="") as f:
        r = csv.DictReader(f)
        for row in r:
            c = row.get("criterion","")
            m = re.match(r"\[Lot:\s*(.+?)\]\s*(.+)", c)
            lot = m.group(1).strip() if m else "_GLOBAL_"
            lots[lot].append(row)

    base = os.path.splitext(args.out)[0]
    for lot, rows in lots.items():
        safe = re.sub(r"[^A-Za-z0-9_]+", "_", lot)
        out_csv = f"{base}_{safe}.csv"
        with open(out_csv, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=["criterion","weight_pct","group","total_pct","price_model","scoring_model","model_anchor","npv_constants"])
            w.writeheader()
            for row in rows:
                npv = ""
                if os.path.exists(ps_path):
                    with open(ps_path, "r", encoding="utf-8", newline="") as pf:
                        pr = csv.DictReader(pf)
                        for prow in pr:
                            try:
                                cst = json.loads(prow.get("constants","") or "{}")
                            except Exception:
                                cst = {}
                            if "discount" in json.dumps(cst).lower() or "kpi" in json.dumps(cst).lower() or "term" in json.dumps(cst).lower():
                                npv = json.dumps(cst, ensure_ascii=False)
                                break
                w.writerow({
                    "criterion": row.get("criterion",""),
                    "weight_pct": row.get("weight_pct",""),
                    "group": row.get("group",""),
                    "total_pct": row.get("total_pct",""),
                    "price_model": row.get("price_model",""),
                    "scoring_model": row.get("scoring_model",""),
                    "model_anchor": row.get("model_anchor",""),
                    "npv_constants": npv
                })
        print(out_csv)
    return 0

if __name__ == "__main__":
    sys.exit(main())
