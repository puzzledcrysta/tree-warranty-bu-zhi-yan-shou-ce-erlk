from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from app.modules.runs.service import run


def test_idempotent(client):
    first = client.post('/api/runs',json={}).json()
    assert first == client.post('/api/runs',json={}).json()
    assert len(client.get('/api/runs').json())==1


def test_keeps_different_book(client,book):
    first = client.post('/api/runs',json={}).json()['manifest']
    second = client.post('/api/runs',json={'book':book.decode()+'\n'}).json()['manifest']
    assert first['source_sha256']==second['source_sha256']
    assert first['run_id']!=second['run_id']


def test_replay_same_result(client):
    result = client.post('/api/runs',json={}).json()
    key = result['manifest']['run_id']
    assert client.post(f'/api/runs/{key}/replay').json() == result


def test_manifest_identifies_data(client,source,book):
    proof = client.post('/api/runs',json={}).json()['manifest']
    assert proof['source_sha256']==sha256(source).hexdigest()
    assert proof['book_sha256']==sha256(book).hexdigest() and proof['elapsed_ms']>=0


def test_failed_run_not_written(client):
    assert client.post('/api/runs',json={'data':'bad\na'}).status_code==422
    assert client.get('/api/runs').json()==[]


def test_concurrent_replays_one_record(client,source,book):
    with ThreadPoolExecutor(max_workers=4) as pool:
        results = list(pool.map(lambda _:run(source,book),range(4)))
    assert all(item==results[0] for item in results)
    assert len(client.get('/api/runs').json())==1


def test_missing_id(client):
    response = client.get('/api/runs/not-found')
    assert (response.status_code,response.json()['code']) == (404,'RUN_UNKNOWN')



def test_encoded_source_keeps_fingerprint(client, source):
    from base64 import b64encode
    expected = client.post('/api/runs', json={}).json()
    encoded = b64encode(source).decode()
    uploaded = client.post('/api/runs',json={'data_base64':encoded})
    assert uploaded.status_code == 200 and uploaded.json() == expected


def test_invalid_source_encoding_is_explicit(client):
    problem = client.post('/api/runs',json={'data_base64':'bad!'})
    assert (problem.status_code,problem.json()['code']) == (422,'ENCODING')
    ambiguous = client.post('/api/runs',json={'data':'x','data_base64':'WA=='})
    assert (ambiguous.status_code,ambiguous.json()['code']) == (422,'CONTRACT')



def test_history_reopens_exact_inputs(client, source, book):
    from base64 import b64decode
    run_id = client.post('/api/runs', json={}).json()['manifest']['run_id']
    restored = client.get(f'/api/runs/{run_id}/source').json()
    assert b64decode(restored['data_base64']) == source
    assert b64decode(restored['book_base64']) == book
