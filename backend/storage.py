import json, os, sqlite3, threading, uuid
from pathlib import Path
from datetime import datetime, timezone
DB=Path(os.environ.get('STUDIO_DATA_DIR',str(Path(__file__).parent/'data'))).expanduser().resolve()/'studio.sqlite3'
LOCK=threading.RLock()
def init():
    DB.parent.mkdir(parents=True,exist_ok=True)
    with sqlite3.connect(DB) as db: db.execute('CREATE TABLE IF NOT EXISTS records (id TEXT PRIMARY KEY, kind TEXT NOT NULL, data TEXT NOT NULL)')
def all_records(kind):
    with LOCK, sqlite3.connect(DB) as db: return [json.loads(r[0]) for r in db.execute('SELECT data FROM records WHERE kind=? ORDER BY rowid DESC',(kind,))]
def get(identifier):
    with LOCK, sqlite3.connect(DB) as db:
        row=db.execute('SELECT data FROM records WHERE id=?',(identifier,)).fetchone()
        return json.loads(row[0]) if row else None
def save(kind,data):
    data=dict(data); data.setdefault('id',str(uuid.uuid4())); data.setdefault('created',datetime.now(timezone.utc).isoformat())
    with LOCK, sqlite3.connect(DB) as db: db.execute('INSERT OR REPLACE INTO records VALUES (?,?,?)',(data['id'],kind,json.dumps(data,allow_nan=False)))
    return data
