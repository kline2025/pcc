import re

def extract_from_itt(text):
    rows=[]
    phase=""
    for raw in text.splitlines():
        line=raw.strip()
        low=line.lower()
        if "prekval" in low:
            phase="prequal"
        elif "tilbud" in low and "dokument" in low:
            phase="offer"
        for m in re.finditer(r'\bDOK\s*0?(\d{1,3})\b', line, flags=re.I):
            code_num=m.group(1)
            code=f"DOK{int(code_num):02d}"
            title=line[m.end():].strip(" :\u2013-")
            rows.append({
                "doc_code":code,
                "title":title,
                "phase":phase or "",
                "mandatory":True,
                "source_file":"ITT.txt",
                "snippet":line
            })
    return rows
