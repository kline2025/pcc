# PCC Schema v1 (Norway)

This document defines the CSV outputs written by PCC runners. All files are UTF-8, LF line endings. Numerics use dot decimals; units appear in the `unit` column when applicable. Every CSV row has a corresponding receipt in `proof/receipts.jsonl`.

## 1) forms_and_constraints.csv
Columns: item, value, source_file, source_snippet
Emitted: always when at least one item is found
Examples:
item,value,source_file,source_snippet
channel,Mercell,Konkurransebestemmelser.pdf,Kommunikasjon via Mercell
bid_validity_months,4,Konkurransebestemmelser.pdf,Vedståelsesfrist 4 måneder
language,nb-NO,Konkurransebestemmelser.pdf,Språk: norsk

## 2) submission_checklist.csv
Columns: doc_code, title, phase, mandatory, source_file, source_snippet
Emitted: when ITT enumerates offer attachments
Examples:
doc_code,title,phase,mandatory,source_file,source_snippet
DOK15,Tilbudsbrev,Offer,True,Konkurransebestemmelser.pdf,DOK15 Tilbudsbrev
DOK18,Prisskjema,Offer,True,Konkurransebestemmelser.pdf,DOK18 Prisskjema

## 3) criteria_and_formula.csv
Columns: criterion, weight_pct, group, total_pct, price_model, scoring_model, model_anchor
group ∈ {price, quality}
price_model ∈ {proportional_lowest_over_offer, relative_mercell, npv_in_prisskjema}
Per-lot convention: encode lot in the criterion field as "[Lot: <lot_name>] <criterion_name>". total_pct is scoped per lot (each lot sums to ~100).
Examples:
criterion,weight_pct,group,total_pct,price_model,scoring_model,model_anchor
[Lot: Kontorrekvisita] Pris,70,price,100,proportional_lowest_over_offer,10×(laveste/tilbudt),Bilag 1 Prisskjema
[Lot: Batterier] Miljø,30,quality,100,,absolutt metode 0–10,Kravspesifikasjon §6.4

## 4) price_schema.csv
Columns: sheet, headers, constants
constants is a JSON string
Examples:
sheet,headers,constants
NS3420_Beskrivelse,"Kapittel|Postnr|NS3420|Beskrivelse|Enhet|Mengde","{""ns3420_version"":""2023"",""includes_regningsarbeider"":true}"
SSA_V_Maintenance,"Linjenr.|Oppdragsgivers beskrivelse|Antatt mengde pr. år|Enhet|Tilbudt pris pr enhet for vedlikehold|Totalsum pr. år","{""support_categories"":[""A"",""B"",""C""],""billing_period"":""monthly""}"
Forsyningssenter_rabatt,"Kunde/forrsyningssenter|Rabatt_pct","{""regions"":[""HSØ"",""Øvrige""],""weights"":{""HSØ"":0.30,""Øvrige"":0.05}}"

## 5) requirements_matrix.csv
Columns: id, section, kind, prompt_kind, text, value_hint, source_file, source_snippet
kind ∈ {mandatory, mandatory_info, optional, evaluation}
prompt_kind ∈ {boolean, value, description, attachment, mixed}
Examples:
id,section,kind,prompt_kind,text,value_hint,source_file,source_snippet
G1.0,Generelle krav,mandatory,boolean,Bekreft at...,bekreft,Kravspesifikasjon.pdf,Rad G1.0
V5.3,Samhandling,mandatory,boolean,Minst 2 statusmøter pr år,2 pr år,Kravspesifikasjon.pdf,§V5.3
SL2,Service levels,description,description,Servicenivå 2 inkluderer...,SL2,SLA-bilag.docx,Kap. 2.1

## 6) service_sla.csv
Columns: key, value, unit, text, source_file, source_snippet
Emitted: for service/IT packs with SLA language
Examples:
key,value,unit,text,source_file,source_snippet
sla:severity:A:response_hours,1,h,Responstid P1,SLA-bilag.docx,Tabell 1
sla:uptime_target_pct,99.9,%,Oppetid pr kalendermåned,SLA-bilag.docx,§4.2

## 7) contract_terms.csv
Columns: key, value, unit, source_file, source_snippet
Keys are namespaced. Examples:
delay_ld:rate_pct_per_working_day,0.25,%,Rammeavtale.pdf,0,25 % per virkedag
payment:days,30,,Rammeavtale.pdf,Betalingsfrist 30 dager
edi:ehf_required,true,,Elektronisk samhandlingsavtale.pdf,EHF påkrevd
dps:rolling_admission,true,,Kvalifikasjonsgrunnlag DPS.pdf,fortløpende opptak

## 8) variants.csv
Columns: variant, in_itt, in_price, in_contracts
Binary flags encoded as 0/1
Example:
variant,in_itt,in_price,in_contracts
Leie,1,1,1

## 9) cross_refs.csv
Columns: topic, spec_value, contract_value, unit_spec, unit_contract
Examples:
topic,spec_value,contract_value,unit_spec,unit_contract
ld_day_unit_alignment,arbeidsdag,kalenderdag,day,day
env_thresholds_alignment,"pH 6,0–8,5","pH 6.0–8.5",pH,pH

## 10) submission_checklist.csv
Columns: doc_code, title, phase, mandatory, source_file, source_snippet

## Retired files
service_levels.csv and evaluation_items.csv are retired. Use service_sla.csv and requirements_matrix.csv.

