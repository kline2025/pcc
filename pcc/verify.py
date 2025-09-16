from __future__ import annotations
def main(argv=None) -> int:
    import argparse
    from .merkle import merkle_root
    ap = argparse.ArgumentParser(prog="pcc-verify", description="Recompute Merkle root over receipts.jsonl and compare to root.txt")
    ap.add_argument("--receipts", required=True, help="Path to receipts.jsonl")
    ap.add_argument("--root", required=True, help="Path to root.txt")
    args = ap.parse_args(argv)
    with open(args.receipts, "rb") as f:
        lines = f.read().splitlines(keepends=True)
    computed = merkle_root(lines)
    want = None
    with open(args.root, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("root:"):
                want = line.split(":",1)[1].strip()
                break
    ok = bool(want) and computed == want
    print(f'{{"verified": {str(ok).lower()}, "computed":"{computed}","expected":"{want or ""}"}}')
    return 0 if ok else 1
if __name__ == "__main__":
    raise SystemExit(main())
