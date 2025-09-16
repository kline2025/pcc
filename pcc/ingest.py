from __future__ import annotations
import os, zipfile, hashlib
ALLOWED_EXT = {".pdf", ".docx", ".txt", ".csv", ".xlsx"}
def sha256_hex(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()
def iter_zip_members(zip_path: str):
    out = []
    with zipfile.ZipFile(zip_path, "r") as z:
        for info in z.infolist():
            if info.is_dir():
                continue
            name = info.filename
            ext = os.path.splitext(name)[1].lower()
            data = z.read(info)
            out.append({
                "name": name,
                "ext": ext,
                "size": info.file_size,
                "sha256": sha256_hex(data),
                "allowed": ext in ALLOWED_EXT,
                "is_text": ext in {".txt", ".csv"},
                "preview": data[:2000].decode("utf-8", errors="ignore") if ext in {".txt", ".csv"} else ""
            })
    return out
