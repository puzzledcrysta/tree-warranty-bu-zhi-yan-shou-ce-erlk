import json
from datetime import datetime, timezone
from time import perf_counter
from app.manifest import manifest
from app.pipeline import execute
from .repository import fetch, persist


def run(source,book):
    proof = manifest(source,book)
    started = perf_counter()
    result = execute(source,book)
    created = datetime.now(timezone.utc).isoformat()
    proof.update(elapsed_ms=round((perf_counter()-started)*1000,2),created=created)
    result['manifest'] = proof
    stored = persist(proof['run_id'],source,book,result,created)
    return json.loads(stored['result'])


def replay(run_id):
    old = fetch(run_id)
    return run(old['source'],old['book'])


def get(run_id):
    return json.loads(fetch(run_id)['result'])
