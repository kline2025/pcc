def build_cross_refs(spec_params: dict, contract_terms: dict):
    rows=[]
    def add(topic, skey, ckey, unit_s=None, unit_c=None):
        sv = spec_params.get(skey)
        cv = contract_terms.get(ckey)
        if sv is not None or cv is not None:
            rows.append({
                'topic': topic,
                'spec_value': sv if sv is not None else '',
                'contract_value': cv if cv is not None else '',
                'unit_spec': spec_params.get('spec:ld_day_unit','') if unit_s else '',
                'unit_contract': contract_terms.get('leie:ld_day_unit', contract_terms.get('eie:ld_day_unit','')) if unit_c else ''
            })
    add('handover_months_max', 'spec:handover_months_max', 'eie:takeover_max_months_after_sign')
    add('delay_ld_nok_per_day', 'spec:delay_ld_nok_per_day', 'eie:delay_ld_nok_per_day', unit_s=True, unit_c=True)
    add('delay_ld_nok_per_day', 'spec:delay_ld_nok_per_day', 'leie:ld_per_day_fraction', unit_s=True, unit_c=True)
    return rows
