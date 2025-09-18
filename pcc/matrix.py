import os,csv,json
def _ensure(outdir): os.makedirs(outdir,exist_ok=True)
def write_requirements_csv(outdir, rows):
    _ensure(outdir); fn=os.path.join(outdir,'requirements.csv')
    with open(fn,'w',newline='') as fp:
        w=csv.writer(fp); w.writerow(['req_id','priority','doc','doc_sha256','char_start','char_end','text_snippet'])
        for r in rows: w.writerow([r.get('req_id'),r.get('priority'),r.get('doc'),r.get('doc_sha256'),r.get('char_start'),r.get('char_end'),r.get('text_snippet')])
def write_compliance_csv(outdir, rows):
    _ensure(outdir); fn=os.path.join(outdir,'compliance.csv')
    with open(fn,'w',newline='') as fp:
        w=csv.writer(fp); w.writerow(['req_id','state','state_reason'])
        for r in rows: w.writerow([r.get('req_id'),r.get('state'),r.get('state_reason')])
def write_price_schema_csv(outdir, sheet_name, header_list, constants):
    _ensure(outdir); fn=os.path.join(outdir,'price_schema.csv'); mode='a' if os.path.exists(fn) else 'w'
    with open(fn,mode,newline='') as fp:
        w=csv.writer(fp)
        if mode=='w': w.writerow(['sheet','headers','constants'])
        w.writerow([sheet_name,"|".join(header_list),json.dumps(constants,ensure_ascii=False)])
def write_service_levels_csv(outdir, features):
    _ensure(outdir); fn=os.path.join(outdir,'service_levels.csv')
    with open(fn,'w',newline='') as fp:
        w=csv.writer(fp); w.writerow(['feature_key','feature_text','sl0_included','sl1_included','sl2_included','param_name','param_required','ref_requirement_id'])
        for r in features: w.writerow([r['feature_key'],r['feature_text'],r['sl0_included'],r['sl1_included'],r['sl2_included'],r['param_name'],r['param_required'],r['ref_requirement_id']])
def write_contract_terms_csv(outdir, terms_dict):
    _ensure(outdir); fn=os.path.join(outdir,'contract_terms.csv')
    with open(fn,'w',newline='') as fp:
        w=csv.writer(fp); w.writerow(['key','value'])
        for k in sorted(terms_dict.keys()): w.writerow([k,terms_dict[k]])
def write_requirements_matrix_csv(outdir, rows):
    _ensure(outdir); fn=os.path.join(outdir,'requirements_matrix.csv')
    with open(fn,'w',newline='') as fp:
        w=csv.writer(fp); w.writerow(['req_id','section','kind','prompt_kind','value_hint','krav_text','source_file','source_sheet','source_row'])
        for r in rows: w.writerow([r.get('req_id',''),r.get('section',''),r.get('kind',''),r.get('prompt_kind',''),r.get('value_hint',''),r.get('krav_text',''),r.get('source_file',''),r.get('source_sheet',''),r.get('source_row','')])
def write_evaluation_items_csv(outdir, rows):
    _ensure(outdir); fn=os.path.join(outdir,'evaluation_items.csv')
    with open(fn,'w',newline='') as fp:
        w=csv.writer(fp); w.writerow(['eval_id','section','priority_rank','criterion','prompt_kind','krav_text','source_file','source_sheet','source_row'])
        for r in rows: w.writerow([r.get('eval_id',''),r.get('section',''),r.get('priority_rank',''),r.get('criterion',''),r.get('prompt_kind',''),r.get('krav_text',''),r.get('source_file',''),r.get('source_sheet',''),r.get('source_row','')])
def write_forms_constraints_csv(outdir, rows):
    _ensure(outdir); fn=os.path.join(outdir,'forms_and_constraints.csv')
    with open(fn,'w',newline='') as fp:
        w=csv.writer(fp); w.writerow(['item','value','source_file','source_snippet'])
        for r in rows: w.writerow([r.get('item',''),r.get('value',''),r.get('source_file',''),r.get('source_snippet','')])


def write_addenda_diff_csv(outdir, rows):
    _ensure(outdir)
    fn=os.path.join(outdir,'addenda_diff.csv')
    if not rows:
        return
    with open(fn,'w',newline='') as fp:
        w=csv.writer(fp)
        w.writerow(['field','before_value','after_value','source_old','source_new'])
        for r in rows:
            w.writerow([r.get('field',''),r.get('before',''),r.get('after',''),r.get('source_old',''),r.get('source_new','')])
