.PHONY: setup check-poppler preflight sandbox riskcard ci

setup:
	python3 -m venv .venv; . .venv/bin/activate; pip install -r requirements.txt || true

check-poppler:
	./scripts/check_poppler.sh

preflight:
	. .venv/bin/activate; LAST=$(ls -d out/run-*/matrix 2>/dev/null | tail -n 1); test -n "$$LAST"; python3 scripts/cli/pcc_preflight.py --matrix "$$LAST" --out preflight_sample.csv

sandbox:
	. .venv/bin/activate; M=$(dirname "$(find out golden -type f -name criteria_and_formula.csv | head -n 1)"); test -n "$$M"; python3 scripts/cli/pcc_sandbox.py --matrix "$$M" --out sandbox_sample.csv

riskcard:
	. .venv/bin/activate; M=$(dirname "$(find out golden -type f -name contract_terms.csv | head -n 1)"); test -n "$$M"; python3 scripts/cli/pcc_riskcard.py --matrix "$$M" --format md --out risk_sample.md

ci:
	bash scripts/ci_run.sh
