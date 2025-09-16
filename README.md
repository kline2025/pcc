# PCC — Procurement Coherence & Compliance (skeleton)

Deterministic, receipts-first CLI tools that digest a tender (and optionally an offer) into
portable proofs.

## Install
python3 -m venv .venv && source .venv/bin/activate && pip install -e .

## Demo
pcc-digest --tender-zip samples/tender-min.zip --out out/run-1
pcc-verify --receipts out/run-1/proof/receipts.jsonl --root out/run-1/proof/root.txt
