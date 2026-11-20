import json
from app.errors import DataError
from app.store import connection


def lookup(db,run_id):
    row = db.execute('SELECT * FROM runs WHERE id=?',(run_id,)).fetchone()
    if row is None:
        raise DataError('RUN_UNKNOWN','没有此批次',404)
    return row


def fetch(run_id):
    with connection() as db:
        return lookup(db,run_id)


def persist(run_id,source,book,result,created):
    with connection() as db:
        db.execute('INSERT OR IGNORE INTO runs VALUES (?,?,?,?,?)',
                   (run_id,source,book,json.dumps(result,ensure_ascii=False),created))
        return lookup(db,run_id)


def history():
    with connection() as db:
        return [dict(row) for row in db.execute('SELECT id,created FROM runs ORDER BY created DESC,id DESC LIMIT 50')]
