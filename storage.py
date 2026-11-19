"""Local persistent results for the capstone prototype."""
import json
import sqlite3
from pathlib import Path
from datetime import datetime, timezone
from uuid import uuid4
DATA = Path(__file__).parent/'saved_analyses'

def setup():
    DATA.mkdir(exist_ok=True)
    with sqlite3.connect(DATA/'history.db') as db:
        db.execute('CREATE TABLE IF NOT EXISTS analyses (id TEXT PRIMARY KEY, created_at TEXT, source TEXT, mode TEXT, method TEXT, results_json TEXT)')

def save(source, mode, method, stats, original_png, overlay_png, mask_png):
    setup(); ident=uuid4().hex[:12]
    for name,content in [('original',original_png),('overlay',overlay_png),('mask',mask_png)]:
        (DATA/f'{ident}_{name}.png').write_bytes(content)
    with sqlite3.connect(DATA/'history.db') as db:
        db.execute('INSERT INTO analyses VALUES(?,?,?,?,?,?)', (ident,datetime.now(timezone.utc).isoformat(),source,mode,method,json.dumps(stats)))
    return ident

def history():
    setup()
    with sqlite3.connect(DATA/'history.db') as db:
        return list(db.execute('SELECT id,created_at,source,mode,method,results_json FROM analyses ORDER BY created_at DESC LIMIT 50'))
