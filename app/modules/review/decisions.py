import json
import sqlite3
from datetime import datetime, timezone
from app.errors import DataError
from app.store import connection
from app.pipeline import execute, stages
from app.modules.runs.repository import lookup

ADOPT = '采信'
CONFIRM = '确认'
RETURN = '退回'
COLS = 'version,decision,note,changed,kind,key,revision,line,digest'


def entries(db,run_id):
    return list(map(dict,db.execute(
        f'SELECT {COLS} FROM reviews WHERE run_id=? ORDER BY version DESC',(run_id,))))


def timeline(run_id):
    with connection() as db:
        lookup(db,run_id)
        return entries(db,run_id)


def _pool(record,key):
    base = stages(record['source'])
    return [row for row in base['quality']['conflicts']
            if row['key']==key and row['code']=='REV_CONFLICT']


def _match(pool,revision,line,digest):
    return [row for row in pool if row['revision']==revision and row['line']==line
            and (digest is None or row.get('digest')==digest)]


def live(record,entry):
    """A ruling holds only while its exact source is still the highest revision."""
    pool = _pool(record,entry['key'])
    if not pool or entry['revision'] != max(row['revision'] for row in pool):
        return None
    chosen = _match(pool,entry['revision'],entry['line'],entry['digest'])
    return chosen[0] if len(chosen)==1 else None


def _latest(db):
    """One newest 采信 entry per 街段验收单, across every saved batch.

    Rulings are keyed by 街段验收单 rather than by batch, so a higher revision
    filed later supersedes the older verdict even though it lands in a new
    batch. ``live`` re-checks each entry against the batch being computed.
    """
    latest = {}
    for row in db.execute(f'SELECT {COLS} FROM reviews WHERE kind=? '
                          'ORDER BY changed DESC, rowid DESC',(ADOPT,)):
        latest.setdefault(dict(row)['key'],dict(row))
    return latest


def rulings(db=None):
    if db is not None:
        return _latest(db)
    with connection() as db:
        return _latest(db)


def decisions(db=None):
    return rulings(db)


def _refresh(db,run_id,record):
    stored = json.loads(record['result'])
    fresh = execute(record['source'],record['book'],decisions(db))
    fresh['manifest'] = stored['manifest']
    db.execute('UPDATE runs SET result=? WHERE id=?',(json.dumps(fresh,ensure_ascii=False),run_id))
    return fresh


def _version(db,run_id):
    return db.execute('SELECT COALESCE(MAX(version),0)+1 FROM reviews WHERE run_id=?',
                      (run_id,)).fetchone()[0]


def adopt(run_id,choice):
    """复核员在异常巡检里采信一份可信原始底单，用它复算合格株数。

    One verdict per 街段验收单 lands in 签收底稿. The identical retry returns
    the first entry without adding a duplicate; a competing verdict on a
    still-live key is refused, so only one ruling takes effect. A higher
    revision filed later leaves the old ruling unable to match, so it lapses
    and a fresh verdict can be recorded.
    """
    note = choice.note.strip()
    if not note:
        raise DataError('REVIEW_NOTE','采信原始底单须填写复核意见')
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        record = lookup(db,run_id)
        current = rulings(db).get(choice.key)
        if current and (current['revision'],current['line'],current['digest']) == \
                (choice.revision,choice.line,choice.digest):
            # Same ruling retried: keep the first record, never ledger it twice.
            return current, _refresh(db,run_id,record)
        pool = _pool(record,choice.key)
        if not pool:
            raise DataError('REVIEW_DECISION','该街段当前没有待采信的冲突来源')
        chosen = _match(pool,choice.revision,choice.line,choice.digest)
        if len(chosen)!=1:
            raise DataError('REVIEW_DECISION','所选原始底单与当前批次不一致，请刷新后重选')
        if choice.revision != max(row['revision'] for row in pool):
            raise DataError('REVIEW_DECISION','只能采信最高修订的原始底单')
        chosen = chosen[0]
        if current and live(record,current):
            raise DataError('RULING_EXISTS','该街段已有生效裁决，不能并行采信另一份底单',409)
        entry = {'version':_version(db,run_id),'decision':ADOPT,'note':note,
                 'changed':datetime.now(timezone.utc).isoformat(),'kind':ADOPT,
                 'key':choice.key,'revision':choice.revision,'line':chosen['line'],
                 'digest':chosen['digest']}
        db.execute(f'INSERT INTO reviews(run_id,{COLS}) VALUES (?,?,?,?,?,?,?,?,?,?)',
                   (run_id,*entry.values()))
        return entry, _refresh(db,run_id,record)


def decide(run_id,version,decision,note):
    note = note.strip()
    if decision not in {CONFIRM,RETURN}:
        raise DataError('REVIEW_DECISION','复核结论无效')
    with connection() as db:
        db.execute('BEGIN IMMEDIATE')
        run = json.loads(lookup(db,run_id)['result'])
        current = db.execute('SELECT COALESCE(MAX(version),0) FROM reviews WHERE run_id=?',
                             (run_id,)).fetchone()[0]
        if current != version:
            raise DataError('STALE','复核版本已过期，请刷新',409)
        if (run['book']['mismatched'] or run['quarantine'] or decision==RETURN) and not note:
            raise DataError('REVIEW_NOTE','有差异时须填写复核意见')
        record = {'version':current+1,'decision':decision,'note':note,
                  'changed':datetime.now(timezone.utc).isoformat(),'kind':'复核'}
        try:
            db.execute('INSERT INTO reviews(run_id,version,decision,note,changed,kind) '
                       'VALUES (?,?,?,?,?,?)',(run_id,*record.values()))
        except sqlite3.IntegrityError as error:
            # A racing writer claimed this version; only one verdict may land.
            raise DataError('STALE','复核版本已过期，请刷新',409) from error
        return record
