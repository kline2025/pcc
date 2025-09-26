# PCC Decision JSON v1

Runners write a single JSON record to stdout (and a short reason to stderr). Checks array contains named flags.

## Canonical checks (keys)
tender:pack:parse_ok
tender:criteria:weights_disclosed
tender:criteria:price_model_present
tender:criteria:weights_sum_100
tender:price:schema_captured
tender:contract:terms_extracted
tender:service_sla:present
tender:dpa:present
tender:lots:detected
tender:variants:declared
tender:dps:enabled
tender:dps:criteria_at_calloff

weights_sum_100 is scoped per lot when lots exist; otherwise global.

## Exit codes
0 allow, 1 block (advice), 2 block (enforce)

## Reason line
allow because ok, window 5m
blocked because <token>, held 5m

