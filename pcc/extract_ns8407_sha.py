import re
from typing import List, Dict, Tuple

def _row(req_id, section, kind, prompt_kind, value_hint, krav_text, src, src_row):
    return {"req_id":req_id,"section":section,"kind":kind,"prompt_kind":prompt_kind,"value_hint":value_hint,"krav_text":krav_text,"source_file":src,"source_row":src_row}

def extract_sha_plan(text: str, src_file: str) -> Tuple[List[Dict], List[Dict]]:
    R: List[Dict] = []
    RC: List[Dict] = []

    # 0.2.1 – Vedlegg som skal brukes
    R.append(_row("SHA-ATT-OPPSLAG","Oppslagstavle","mandatory","attachment","sjekkliste skal benyttes","Sjekkliste for oppslagstavle på byggeplass skal benyttes.",src_file,"§0.2.1"))
    R.append(_row("SHA-ATT-VARSLING","Varslingsplan","mandatory","attachment","skal henges opp","Varslingsplan skal benyttes og henges opp på oppslagstavle og andre hensiktsmessige steder.",src_file,"§0.2.1"))
    R.append(_row("SHA-ATT-SKADE","Rapportering av skade","mandatory","attachment","Statsbygg-skjema","Skjema for rapportering av skade/potensiell skade skal benyttes.",src_file,"§0.2.1"))
    R.append(_row("SHA-ATT-BERED","Beredskapsplan","mandatory","attachment","prosjektspesifikk","Beredskapsplan på byggeplass skal benyttes.",src_file,"§0.2.1"))

    # 2.2 – Produksjonsplaner synlig 2–4 uker frem
    R.append(_row("SHA-PRODPLAN-POST","Fremdrift/produksjon","mandatory","boolean","rullerende 2–4 uker","Detaljerte fremdriftsplaner for neste 2–4 uker skal henge på oppslagstavlen; risikofylte aktiviteter markeres; TE utarbeider/oppdaterer og henger opp.",src_file,"§2.2"))

    # 2.1 – Milepæler (som informasjonsrader for styring)
    R.append(_row("MS-BYGGESTART","Milepæl","mandatory","description","2. kvartal 2024","Byggestart planlagt 2. kvartal 2024.",src_file,"§2.1"))
    R.append(_row("MS-PRØVEDRIFT","Milepæl","mandatory","description","3. kvartal 2025","Ferdigstillelse bygg og oppstart prøvedrift (foreløpig) 3. kvartal 2025.",src_file,"§2.1"))
    R.append(_row("MS-OVERTAK","Milepæl","mandatory","description","3. kvartal 2026","K210 overtakelse fra totalentreprenør (foreløpig) 3. kvartal 2026.",src_file,"§2.1"))
    R.append(_row("MS-SCANNER-INN","Milepæl","mandatory","description","1.–2. kvartal 2025","Inntransport av K313 skannersystem for kjøretøy 1.–2. kvartal 2025.",src_file,"§2.1"))
    R.append(_row("MS-SCANNER-TEST","Milepæl","mandatory","description","2. kvartal 2025","Godkjent funksjonstest K313 skannersystem 2. kvartal 2025.",src_file,"§2.1"))

    # 3 – Risikofylte arbeider (nr. 1–17)
    R.append(_row("SHA-RISK-01","Rydding/skogsarbeid nær vei","mandatory","attachment","plan + kompetanse","Planlegg arbeid i god tid; bruk kompetent personell; etabler tiltak som hindrer at trær faller over vei/gang-/sykkelsti.",src_file,"§3 tabell #1"))
    R.append(_row("SHA-RISK-02","Kulturminne","mandatory","boolean","gjerde ut kulturminne","Plasser byggeplassgjerde slik at kulturminner ligger utenfor byggeplass.",src_file,"§3 tabell #2"))
    R.append(_row("SHA-RISK-03","Bergsprengning","mandatory","value","oppstartsmøte ≥2 uker før","Oppstartsmøte med byggherre senest 2 uker før første salve; følg Statsbygg/Vegvesenet-rutiner; forsiktig sprengning.",src_file,"§3 tabell #3"))
    R.append(_row("SHA-RISK-04","Kvikkleire","mandatory","attachment","supplerende geoteknikk","Sett deg inn i geoteknisk notat; ansvarlig RIG vurderer; spesifiser tiltak i detaljprosjektering.",src_file,"§3 tabell #4"))
    R.append(_row("SHA-RISK-05","Udetonerte forsagere","mandatory","attachment","RIG vurdering + eksplosivsøkshund","Kartlegg og vurder med RIG; bruk eksplosivsøkshund ved behov.",src_file,"§3 tabell #5"))
    R.append(_row("SHA-RISK-06","Trafikk inn/ut – offentlig vei","mandatory","attachment","trafikksikring/arbeidsvarsling","Etabler trafikk­sikring og arbeidsvarsling ved behov.",src_file,"§3 tabell #6"))
    R.append(_row("SHA-RISK-07","Maskiner på byggeplass","mandatory","description","separasjon + ryggevakt","Fysisk skill gående fra kjørende; minimer rygging; etabler tiltak som hindrer personell bak ryggende maskin; bruk ryggevakt.",src_file,"§3 tabell #7"))
    R.append(_row("SHA-RISK-08","Bekk i dagen","mandatory","attachment","arbeidsvarsling","Planlegg arbeid; etabler arbeidsvarsling.",src_file,"§3 tabell #8"))
    R.append(_row("SHA-RISK-09","Kommunalt VA – tilkomst","mandatory","boolean","alltid tilgjengelig","Tilkomst til kommunalt VA-anlegg skal være på utsiden av byggeplass; sikker tilkomst for drift til enhver tid.",src_file,"§3 tabell #9"))
    R.append(_row("SHA-RISK-10","Brakkerigg – tilkomst","mandatory","boolean","sikker tilkomst utenom byggeplass","Riggplan skal beskrive sikker tilkomst til brakkerigg uten å gå via byggeplass.",src_file,"§3 tabell #10"))
    R.append(_row("SHA-RISK-11","Grønt tak – drift","mandatory","boolean","rekkverk på grønt tak","Etabler rekkverk for grønt tak for sikker drift/vedlikehold.",src_file,"§3 tabell #11"))
    R.append(_row("SHA-RISK-12","Fjellskjæring blir stående","mandatory","attachment","fjellsikring ved behov","Fjellsikring av skjæring ved behov; vurderes av RIG.",src_file,"§3 tabell #12"))
    R.append(_row("SHA-RISK-13","Høyspentkabler i grunn","mandatory","attachment","markér trase; følg kabeleier","Marker traseer; informer utførende; følg kabeleiers retningslinjer ved arbeid nær høyspent.",src_file,"§3 tabell #13"))
    R.append(_row("SHA-RISK-14","UVC-lys test","mandatory","boolean","avsperring + kompetanse","Testing kun av kompetent personell; området sperres for uvedkommende.",src_file,"§3 tabell #14"))
    R.append(_row("SHA-RISK-15","Trafikk i driftsfase","mandatory","boolean","separasjon","Skille gående/syklende og biler i utenomhusplan for driftsfase.",src_file,"§3 tabell #15"))
    R.append(_row("SHA-RISK-16","Adgang 3. part","mandatory","boolean","elektronisk port/ronde ll HMS-kort","Etabler elektronisk styrte porter og rondeller aktivert med HMS-kort.",src_file,"§3 tabell #16"))
    R.append(_row("SHA-RISK-17","Vedlikehold fasader/tak","mandatory","description","tilkomst for lift","Utarbeid utenomhusplan slik at lift kan kjøre rundt byggene.",src_file,"§3 tabell #17"))

    return R, RC
