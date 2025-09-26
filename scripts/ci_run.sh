#!/usr/bin/env bash
set -e
echo "ci: poppler check"
./scripts/check_poppler.sh >/dev/null
echo "ci: locate matrices"
MATRIX_WITH_CRIT=$(dirname "$(find golden out -type f -name criteria_and_formula.csv 2>/dev/null | head -n 1)")
MATRIX_WITH_CT=$(dirname "$(find golden out -type f -name contract_terms.csv 2>/dev/null | head -n 1)")
if [ -z "$MATRIX_WITH_CRIT" ]; then echo "no matrix with criteria found"; exit 2; fi
if [ -z "$MATRIX_WITH_CT" ]; then echo "no matrix with contract_terms found"; exit 2; fi
echo "ci: run preflight"
python3 scripts/cli/pcc_preflight.py --matrix "$MATRIX_WITH_CT" --out /tmp/preflight.csv >/dev/null
echo "ci: run sandbox"
python3 scripts/cli/pcc_sandbox.py --matrix "$MATRIX_WITH_CRIT" --out /tmp/sandbox.csv >/dev/null
echo "ci: run riskcard"
python3 scripts/cli/pcc_riskcard.py --matrix "$MATRIX_WITH_CT" --format md --out /tmp/risk.md >/dev/null
echo "ci: verify goldens exist"
count=$(find golden -type f -name receipts.jsonl | wc -l | awk '{print $1}')
if [ "$count" -lt 1 ]; then echo "no golden receipts present"; exit 2; fi
echo "ci: ok"
