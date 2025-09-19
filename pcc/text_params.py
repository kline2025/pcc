import re

def scan_text_params(text):
    params = {}
    receipts = []

    m = re.search(r'(overtakelse|overlevering|innflytting)[^\n\r]{0,60}(\d{1,3})\s*måneder', text, flags=re.I)
    if m:
        val = int(m.group(2))
        params['spec:handover_months_max'] = val
        receipts.append({'type':'spec_param','key':'handover_months_max','value':val,'unit':'months','snippet':m.group(0)})

    m = re.search(r'(dagmulkt|dagbot|forsinkelse)[^\n\r]{0,80}([0-9][0-9 .]{1,12})\s*(kr|kroner)[^\n\r]{0,30}\bper\b[^\n\r]{0,5}(arbeidsdag|kalenderdag)', text, flags=re.I)
    if m:
        raw = m.group(2)
        val = int(raw.replace(' ', '').replace('.', ''))
        unit = 'working_day' if m.group(4).lower().startswith('arbeids') else 'calendar_day'
        params['spec:delay_ld_nok_per_day'] = val
        params['spec:ld_day_unit'] = unit
        receipts.append({'type':'spec_param','key':'delay_ld_nok_per_day','value':val,'unit':unit,'snippet':m.group(0)})

    return params, receipts
