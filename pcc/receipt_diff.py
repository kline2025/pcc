from __future__ import annotations
import json
def main(argv=None) -> int:
    import argparse
    ap = argparse.ArgumentParser(prog="pcc-receipt-diff", description="Diff two receipts.jsonl files at node level")
    ap.add_argument("--old", required=True)
    ap.add_argument("--new", required=True)
    args = ap.parse_args(argv)
    def load(path):
        rows = []
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rows.append(json.loads(line))
        return rows
    a = load(args.old)
    b = load(args.new)
    sa = {json.dumps(r, sort_keys=True) for r in a}
    sb = {json.dumps(r, sort_keys=True) for r in b}
    added = [json.loads(s) for s in sb - sa]
    removed = [json.loads(s) for s in sa - sb]
    out = {"added": added, "removed": removed, "added_count": len(added), "removed_count": len(removed)}
    print(json.dumps(out, ensure_ascii=False))
    return 0
if __name__ == "__main__":
    raise SystemExit(main())
