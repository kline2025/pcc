import hashlib, json, os
from datetime import datetime, timezone
from .version import VERSION

def merkle_root(lines):
    h = hashlib.sha256()
    for b in lines:
        h.update(b)
    return h.hexdigest()

def _canon_line(obj):
    return (json.dumps(obj, ensure_ascii=False, separators=(',', ':'), sort_keys=True) + '\n').encode('utf-8')

def write_receipts_and_root(receipts_path, root_path, rows):
    os.makedirs(os.path.dirname(receipts_path), exist_ok=True)
    os.makedirs(os.path.dirname(root_path), exist_ok=True)
    canon_lines = [_canon_line(r) for r in rows]
    with open(receipts_path, 'wb') as f:
        for b in canon_lines:
            f.write(b)
    root_hex = merkle_root(canon_lines)
    ts = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    with open(root_path, 'w', encoding='utf-8', newline='\n') as g:
        g.write(f'root: {root_hex}\n')
        g.write(f'lines: {len(canon_lines)}\n')
        g.write(f'ts: {ts}\n')
        g.write(f'tool_version: {VERSION}\n')
        g.write('git_sha: dev\n')
    return root_hex
