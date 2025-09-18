import re, json
def extract(text, asset_id):
    t = text.lower()
    rows = []
    def add(key, needle, sl0, sl1, sl2, param_name=None, ref=None):
        if needle.lower() in t:
            rows.append({
                "feature_key": key,
                "feature_text": needle,
                "sl0_included": sl0,
                "sl1_included": sl1,
                "sl2_included": sl2,
                "param_name": param_name or "",
                "param_required": bool(param_name),
                "ref_requirement_id": ref or "",
                "source_snippet": needle
            })
    add("time_price_only","Timepris for arbeid",True,False,False,None,None)
    add("preventive_maintenance","Preventivt vedlikehold",False,True,True,None,None)
    add("pv_parts_and_recommended","Deler som inngår i produsentens PV",False,True,True,None,None)
    add("safety_check","Sikkerhetskontroll",False,True,True,None,None)
    add("security_updates","Sikkerhetsoppdateringer",False,True,True,None,None)
    add("spare_parts_lead","Maksimum xx timers (y døgn) leveringstid på reservedeler",True,True,True,"parts_lead_time","L3")
    add("all_service_costs_included","Alle serviceutgifter inkludert",False,False,True,None,None)
    add("acute_response_time","Maksimum oppmøtetid ved akuttservice",False,False,True,"acute_response_time","L5")
    add("phone_support_1h","Telefonsupport innen 1 time",True,True,True,None,None)
    add("os_av_updates","Jevnlig sikkerhetsoppdatering av virusbeskyttelse og operativsystem",True,True,True,None,None)
    add("software_upgrades","Alle Programvareoppdateringer inkludert nye versjoner",True,True,True,None,None)
    receipts = []
    for r in rows:
        receipts.append({
            "type":"service_feature","asset_id":asset_id,
            "key":r["feature_key"],"sl0":r["sl0_included"],"sl1":r["sl1_included"],"sl2":r["sl2_included"],
            "param_name":r["param_name"],"param_required":r["param_required"],
            "ref_requirement_id":r["ref_requirement_id"],"text":r["feature_text"]
        })
    receipts.append({"type":"service_levels","asset_id":asset_id,"features":len(rows)})
    return rows, receipts
