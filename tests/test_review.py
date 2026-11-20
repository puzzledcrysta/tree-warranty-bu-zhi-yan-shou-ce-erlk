import pytest


@pytest.fixture
def anchor(client):
    return client.post('/api/runs',json={}).json()['manifest']['run_id']


def review(client,anchor,version=0,decision='确认',note='已逐条核对外部账'):
    return client.post(f'/api/review/{anchor}',json={'version':version,'decision':decision,'note':note})


def test_stale(client,anchor):
    # TRAP-26
    assert review(client,anchor).json()['version']==1
    stale = review(client,anchor)
    assert (stale.status_code,stale.json()['code'])==(409,'STALE')


def test_noted_differences(client,anchor):
    response = review(client,anchor,note='  ')
    assert (response.status_code,response.json()['code'])==(422,'REVIEW_NOTE')


def test_versioned_history(client,anchor):
    assert review(client,anchor).status_code == 200
    assert review(client,anchor,1,'退回','请补来源旁证').status_code == 200
    assert [item['version'] for item in client.get(f'/api/review/{anchor}').json()] == [2,1]


def test_export_reproducible(client,anchor):
    first = client.get(f'/api/export/{anchor}')
    second = client.get(f'/api/export/{anchor}')
    assert first.content == second.content and 'attachment' in first.headers['content-disposition']


def test_export_carries_source_evidence(client,anchor):
    proof = client.get(f'/api/export/{anchor}').json()
    row = proof['results'][0]
    assert (row['key'],row['line'])==('00101',2)
    assert row['raw'] and row['proof'] and proof['quarantine']


def test_decision_reaches_export(client,anchor):
    assert review(client,anchor).status_code==200
    assert client.get(f'/api/export/{anchor}').json()['review'][0]['decision']=='确认'
