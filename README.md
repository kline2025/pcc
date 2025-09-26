# PCC — Procurement Coherence & Compliance (skeleton)

Deterministic, receipts-first CLI tools that digest a tender (and optionally an offer) into
portable proofs.

## Install
python3 -m venv .venv && source .venv/bin/activate && pip install -e .

## Demo
pcc-digest --tender-zip samples/tender-min.zip --out out/run-1
pcc-verify --receipts out/run-1/proof/receipts.jsonl --root out/run-1/proof/root.txt
## Quickstart
\n```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m pcc.ns8406_simple --tender-zip tenders/sample.zip --out out/run-1758877747
python scripts/cli/pcc_preflight.py --matrix out/run-*/matrix --out preflight_sample.csv
python scripts/cli/pcc_sandbox.py --matrix out/run-*/matrix --out sandbox_sample.csv
python scripts/cli/pcc_riskcard.py --matrix out/run-*/matrix --format md --out risk_sample.md
```
## Pre-commit

pip install pre-commit || true
pre-commit install

