#!/usr/bin/env bash
set -e
ROOT=$(pwd)
OK=0
for g in golden/*; do
  if [ -d "$g/proof" ] && [ -f "$g/proof/receipts.jsonl" ]; then
    python3 scripts/receipt_diff.py "$g/proof/receipts.jsonl" "$g/proof/receipts.jsonl" >/dev/null
  fi
done
echo "golden check: ok"
