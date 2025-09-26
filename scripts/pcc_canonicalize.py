#!/usr/bin/env python3
import argparse, json, os, platform, subprocess, sys, hashlib, datetime

def canonical_line(obj):
    return (json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(',', ':')) + "\n").encode('utf-8')

def sha256_hex(b):
    h = hashlib.sha256(); h.update(b); return h.hexdigest()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--receipts", required=True)
    ap.add_argument("--out-receipts", required=True)
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--run-json", required=True)
    args = ap.parse_args()

    with open(args.receipts, "rb") as f:
        raw_lines = [ln.rstrip(b"\n") for ln in f]
    objs = []
    for ln in raw_lines:
        if not ln:
            continue
        try:
            objs.append(json.loads(ln.decode('utf-8', errors='ignore')))
        except Exception:
            pass

    canon_bytes = b""
    for obj in objs:
        canon_bytes += canonical_line(obj)

    with open(args.out-receipts, "wb") as f:
        f.write(canon_bytes)

    root = sha256_hex(canon_bytes)
    with open(args.out-root, "w", encoding="utf-8", newline="\n") as f:
        f.write(f"root: {root}\n")

    poppler = ""
    try:
        poppler = subprocess.run(["pdftotext", "-v"], capture_output=True, text=True).stderr.strip()
    except Exception:
        poppler = "pdftotext not found"
    run = {
        "schema_version": "no-v1.0",
        "tool": "pcc-canonicalize",
        "git_sha": os.getenv("PCC_GIT_SHA", ""),
        "python": platform.python_version(),
        "os": f"{platform.system()} {platform.release()}",
        "poppler": poppler,
        "ts": datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ"),
        "input_receipts": os.path.abspath(args.receipts),
        "output_receipts": os.path.abspath(args.out-receipts),
        "output_root": os.path.abspath(args.out-root)
    }
    with open(args.run-json, "w", encoding="utf-8", newline="\n") as f:
        json.dump(run, f, ensure_ascii=False, sort_keys=True, separators=(',', ':'))

if __name__ == "__main__":
    sys.exit(main())
