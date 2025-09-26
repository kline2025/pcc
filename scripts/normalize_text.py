#!/usr/bin/env python3
import argparse, sys, unicodedata, re

def normalize_text(s):
    s = s.replace("\u00A0", " ")
    s = s.replace("\r\n", "\n").replace("\r", "\n")
    s = unicodedata.normalize("NFC", s)
    s = s.replace("•", "-").replace("–", "-").replace("—", "-")
    s = re.sub(r"[ \t]+", " ", s)
    return s

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", required=True)
    ap.add_argument("--out", dest="out", required=True)
    args = ap.parse_args()
    with open(args.inp, "r", encoding="utf-8", errors="ignore") as f:
        txt = f.read()
    norm = normalize_text(txt)
    with open(args.out, "w", encoding="utf-8", newline="\n") as f:
        f.write(norm)

if __name__ == "__main__":
    sys.exit(main())
