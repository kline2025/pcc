# PCC Operator Guide (Norway v1)

## Prereqs
Python 3.11.x. UTF-8 shell.

## Setup
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

## PDF to text
pdftotext -layout -enc UTF-8 <in.pdf> <out.txt>
Replace NBSP (U+00A0) with space if needed.

## Zip layout
Put .txt exports and any docx/xlsx into a zip. Runners consume text; binary files may be present.

## Runner globs (zip must contain at least one matching name per section)

ns8406_simple
Konkurransegrunnlag*.txt
*NS 8406*.txt
*BESK*NS3420*.txt
*MOP*.txt
*Overvåk*.txt

ssa_v
*Konkurransebestemmelser*.txt
*SSA-V*generell*.txt
*Bilag*5*SLA*.txt
*Databehandleravtale*.txt
*Servicetilgangsavtale*.txt
*Kundens tekniske plattform*.txt
*Kravspesifikasjon*.txt
*Prisskjema*.txt

multilot_office
*Konkurransebestemmelser*kontorrekvisita*|*batterier*.txt
*Bilag 1* Prisskjema*.txt
*Bilag 2* Kravspesifikasjon*.txt
*Bilag 13* Rammeavtale*.txt
*Bilag 7* Logistikkbetingelser*.txt
*Bilag 9* Elektronisk samhandlingsavtale*.txt

renhold_facility
*Konkurransebestemmelser*Renhold*.txt
*Bilag 1* Kravspesifikasjon*.txt
*Bilag 2* Prisskjema*.txt
*Rammeavtale* Renhold*.txt
*Bilag 3* AKRIM*.txt
*Bilag 4* Egenrapportering*.txt

dps
*Kvalifikasjonsgrunnlag*Dynamisk*.txt

## Run
python -m pcc.ns8406_simple --tender-zip <zip> --out out/run-$(date +%s)
python -m pcc.ssa_v --tender-zip <zip> --out out/run-$(date +%s)
python -m pcc.multilot_office --tender-zip <zip> --out out/run-$(date +%s)
python -m pcc.renhold_facility --tender-zip <zip> --out out/run-$(date +%s)
python -m pcc.dps --tender-zip <zip> --out out/run-$(date +%s)

## Verify
pcc-verify --receipts out/.../proof/receipts.jsonl --root out/.../proof/root.txt

