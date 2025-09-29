# SSA Baselines Runbook (Text-first, Receipts-first)
1) Stage authoritative files:
   dataset/ssa/SSA-<Family>-<Year>/raw/
2) Convert to UTF-8 .txt into:
   dataset/ssa/SSA-<Family>-<Year>/text/
   Confirm non-zero size; first lines readable.
3) Normalize (NBSP→space, NFC, \n, trim) and record size/hash.
4) Run the family baseline:
   SSA-D: scripts/cli/ssa_d_baseline.py --general .../SSA-D_generell.txt --bilag .../SSA-D_bilag.txt --out out/run-ssa-d-<ts>
   SSA-B: scripts/cli/ssa_b_baseline.py --general .../SSA-B_generell.txt --bilag .../SSA-B_bilag.txt --out out/run-ssa-b-<ts>
   (SSA-V, SSA-LR use their runners or family baseline when added.)
5) Proofs:
   Ensure proof/receipts.jsonl exists.
   If root.txt missing, write computed from pcc-verify, then compare via scripts/ci/verify_root_match.py.
6) Freeze golden (matrices + receipts + root):
   golden/ssa/SSA-<Family>-<Year>/{matrix,proof}
7) CI guard (later):
   Run scripts/ci/verify_root_match.py on each golden; fail on mismatch.
Notes:
- One doorway per run; no mixing.
- Templates usually have no criteria_and_formula.csv; that is correct.
- Never mutate out/run-* after completion; create a new run if needed.
