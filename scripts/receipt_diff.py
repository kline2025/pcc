#!/usr/bin/env python3
import argparse, hashlib, json, sys

def read_lines(path):
    with open(path, "rb") as f:
        return [ln.rstrip(b"\n") for ln in f]

def sha(b):
    return hashlib.sha256(b).hexdigest()

def load_index(lines):
    idx = {}
    for b in lines:
        h = sha(b)
        idx[h] = b
    return idx

def summarize(b):
    try:
        obj = json.loads(b.decode("utf-8", "ignore"))
    except Exception:
        return b[:120].decode("utf-8", "ignore")
    keys = ["type","key","asset_id","sheet","item"]
    vals = []
    for k in keys:
        if k in obj:
            vals.append(f"{k}={obj[k]}")
    return ", ".join(vals) if vals else json.dumps(obj)[:160]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("old")
    ap.add_argument("new")
    args = ap.parse_args()

    old_lines = read_lines(args.old)
    new_lines = read_lines(args.new)
    old_idx = load_index(old_lines)
    new_idx = load_index(new_lines)

    old_set = set(old_idx.keys())
    new_set = set(new_idx.keys())

    added = sorted(new_set - old_set)
    removed = sorted(old_set - new_set)
    unchanged = sorted(new_set & old_set)

    print(f"added={len(added)} removed={len(removed)} unchanged={len(unchanged)}")

    if added:
        print("\nADDED:")
        for h in added[:50]:
            print(f"{h} :: {summarize(new_idx[h])}")
        if len(added) > 50:
            print("...")

    if removed:
        print("\nREMOVED:")
        for h in removed[:50]:
            print(f"{h} :: {summarize(old_idx[h])}")
        if len(removed) > 50:
            print("...")

if __name__ == "__main__":
    sys.exit(main())
