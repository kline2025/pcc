from typing import List, Dict, Tuple

def _row(req_id, section, kind, prompt_kind, value_hint, krav_text, src, src_row):
    return {"req_id":req_id,"section":section,"kind":kind,"prompt_kind":prompt_kind,"value_hint":value_hint,"krav_text":krav_text,"source_file":src,"source_row":src_row}

def extract_bim(text_bep:str, src_bep:str, text_eir:str, src_eir:str, text_simba:str, src_simba:str) -> Tuple[List[Dict], Dict, List[Dict]]:
    R=[]; TERMS={}; RC=[]
    if text_bep:
        R.append(_row("BEP-ANSVAR","BIM-plan (BEP)","mandatory","boolean","TE ansvar","TE etablerer/vedlikeholder BIM-gjennomføringsplan; endringer krever BH-aksept.",src_bep,"p.1–2"))
        R.append(_row("BEP-SAMHANDLING","BIM-plan (BEP)","mandatory","attachment","plattform + varslingsrutine","Samhandlingsplattform, filstruktur og varsling beskrives i BEP.",src_bep,"§4.1"))
        R.append(_row("BEP-UTVEKSLING","BIM-plan (BEP)","mandatory","attachment","utvekslingsrutine","Rutiner for utveksling mot BH og internt.",src_bep,"§4.2"))
        R.append(_row("BEP-MØTER","BIM-plan (BEP)","mandatory","boolean","møteplan","Møteplan for BIM-koordinering/tverrfaglige kontroller i BEP.",src_bep,"§4.3"))
        R.append(_row("BEP-MMI","BIM-plan (BEP)","mandatory","attachment","MMI-indeks","MMI bruk/plan beskrives.",src_bep,"§4.4"))
        R.append(_row("BEP-KARTSYS","BIM-plan (BEP)","mandatory","attachment","NN2000; NTM Sone 10; EPSG 5950","Kartsystemtabell fylles ut: NN2000, NTM Sone 10, EPSG 5950.",src_bep,"§5.1"))
        R.append(_row("BEP-NULLPUNKT","BIM-plan (BEP)","mandatory","attachment","felles nullpunkt + origo-figur","Felles nullpunkt og prosjektorigo beskrives.",src_bep,"§5.2–5.3"))
        R.append(_row("BEP-IFC-OPPSETT","BIM-plan (BEP)","mandatory","attachment","IFC-eksportoppsett","Eksportoppsett til IFC pr programvare.",src_bep,"§5.8"))
        R.append(_row("BEP-IKT-LISTE","BIM-plan (BEP)","mandatory","attachment","programvare/plug-ins/hw","IKT-tabell over programvare/plug-ins/maskinvare.",src_bep,"§2.4"))
    if text_eir:
        R.append(_row("EIR10-BEP","EIR leveranser","mandatory","attachment","BEP iht. BEP-mal","Utarbeid og vedlikehold BEP gjennom hele prosjektet.",src_eir,"Tabell 2.2"))
        R.append(_row("EIR07-TFM","EIR leveranser","mandatory","boolean","TFM-merking","TFM-merking iht. prosjektanvisning.",src_eir,"Tabell 2.2"))
        R.append(_row("ARCHIVE-PER-FASE","BIM – arkiv","mandatory","boolean","IFC pr fase; native ved B3.2 og B5.1","Arkiver modeller etter hver fase (IFC). Native ved B3.2/B5.1.",src_eir,"Tabell 2.1"))
    if text_simba:
        TERMS["bim:ifc_required"]="IFC4.0.2.1 (ADD2 TC1)"
        TERMS["bim:bcf_for_issues"]=True
        TERMS["bim:coordination_cadence_days"]=14
        TERMS["bim:file_naming_pattern"]="ENr_BNr_PNr_Di_SD_SNr.ext"
        TERMS["geodesy:datum"]="ETRS89/NTM + NN2000 (EPSG compound)"
        TERMS["bim:base_quantities_required"]=True
        R.append(_row("IFC-VERSJON","BIM – format/versjon","mandatory","value","IFC4.0.2.1 (IFC4 ADD2 TC1)","Prosjektet skal utveksle modeller på IFC4.0.2.1.",src_simba,"G16"))
        R.append(_row("IFC-MASKINVAL","BIM – kvalitet","mandatory","boolean","mvdXML","IFC maskinvaliders mot mvdXML/åpent kravformat.",src_simba,"G21"))
        R.append(_row("IFC-BASEQ","BIM – mengder","mandatory","boolean","BaseQuantities","Eksporter relevante objektklasser med BaseQuantities.",src_simba,"G28"))
        R.append(_row("GEO-EPSG","BIM – georeferering","mandatory","attachment","ETRS89/NTM + NN2000 (EPSG compound)","Georeferering angis ved EPSG compound-kode.",src_simba,"G7"))
        R.append(_row("NO-ROTASJON","BIM – geometri","mandatory","boolean","rotasjon = 0°","Modell skal ikke roteres ift. kart (0°).",src_simba,"G6"))
        R.append(_row("BCF-ISSUES","BIM – avvik","mandatory","boolean","BCF/BCF-server","Avvik i modellen kommuniseres med BCF.",src_simba,"G39"))
        R.append(_row("KOORD-14D","BIM – koordinering","mandatory","boolean","min. hver 14. dag","Tverrfaglig koordinering minst hver 14. dag.",src_simba,"G25"))
        R.append(_row("FILNAVN-MAL","BIM – navngivning","mandatory","attachment","ENr_BNr_PNr_Di_SD_SNr.ext","Filnavn følger mønsteret ENr_BNr_PNr_Di_SD_SNr.ext.",src_simba,"G22"))
    return R, TERMS, RC

def extract_mop(text_mop:str, src_mop:str, text_veil:str, src_veil:str) -> Tuple[List[Dict], List[Dict]]:
    R=[]; RC=[]
    def add(r): R.append(r)
    def row(i,sec,kind,pk,hint,txt,src,sr): add({"req_id":i,"section":sec,"kind":kind,"prompt_kind":pk,"value_hint":hint,"krav_text":txt,"source_file":src,"source_row":sr})
    row("MOP-0.1-OPPDAT","Ledelse/MOP","mandatory","boolean","månedlig","MOP oppdateres minst månedlig; MOP-møter etter hver oppdatering.",src_mop,"Krav 0.1")
    row("MOP-0.5-ISO14001","Ledelse/MOP","mandatory","attachment","NS-EN ISO 14001:2015","Entreprenør skal ha miljøstyringssystem iht. NS-EN ISO 14001:2015.",src_mop,"Krav 0.5")
    row("MOP-1.1-LCA-TALL","Klimagass (NS3720)","mandatory","attachment","A1-A3 ≤148; A5 ≤17; B6 ≤5","Dokumentere total klimagass – A1-A3≤148, A5≤17, B6≤5 kg CO2e.",src_mop,"Krav 1.1")
    row("MOP-1.3-BETONG-PREFAB","Klimagass/Materialer","mandatory","attachment","Lavkarbon A","Prefab betong minst lavkarbon A.",src_mop,"Krav 1.3")
    row("MOP-1.6-ARMERING","Klimagass/Materialer","mandatory","value","slakk ≤0,39; spenn ≤1,87 kg CO2e/kg","Armeringsstål A1–A3 grenseverdier.",src_mop,"Krav 1.6")
    row("MOP-2.1-PASSIV","ENERGI","mandatory","attachment","NS 3701; U-verdier frostfri","Bygg som passivhus; U-verdier for frostfri sone iht. tabell.",src_mop,"Krav 2.1")
    row("MOP-6.1-SORTGRAD","Avfall","mandatory","value","≥90 %; ≥50 % materialgjenv.","Kildesortering ≥90 % og ≥50 % materialgjenvinning.",src_mop,"Krav 6.1")
    row("MOP-6.2-MENGDETAK","Avfall","mandatory","value","≤25 kg/m² BTA","Total avfallsmengde ≤25 kg/m² BTA.",src_mop,"Krav 6.2")
    if text_veil:
        row("VEIL-REP-ADR","Drift/rapportering","mandatory","value","postmottak@nordrefollo.kommune.no","Rapporter sendes til kommunens postmottak.",src_veil,"§4")
        row("VEIL-REP-FREK","Drift/rapportering","mandatory","value","kvartalsvis/månedlig","Rapporteringsfrekvens: kvartalsvis; månedlig ved prøvetakning.",src_veil,"§4")
        row("VEIL-SS-GRENSE","Resipient/overvann","mandatory","value","SS ≤50 mg/l (sårbare)","SS-grense i sårbare vassdrag: ≤50 mg/l etter rensing.",src_veil,"§4")
    return R, RC
