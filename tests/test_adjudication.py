import csv
import io
from concurrent.futures import ThreadPoolExecutor

import pytest


@pytest.fixture
def anchor(client):
    return client.post('/api/runs', json={}).json()['manifest']['run_id']


def source_row(client, anchor, line, key='00899'):
    report = client.get(f'/api/runs/{anchor}').json()
    for bucket in ('quarantine', 'suppressed'):
        for row in report[bucket]:
            if row['key'] == key and row['line'] == line:
                return row
    raise AssertionError(f'第 {line} 行不在批次中')


def conflict(client, anchor, line, key='00899', revision=2, note='采信巡检卡签字的那份'):
    row = source_row(client, anchor, line, key)
    return client.post(f'/api/adjudicate/{anchor}', json={
        'key': key, 'revision': revision, 'line': line, 'digest': row['digest'], 'note': note,
    })


def test_adopting_original_recomputes_accepted_stems(client, anchor):
    # TRAP-14: without a ruling the conflicting key is isolated and nothing is
    # paid; once the reviewer trusts a source 合格株数 follows that source.
    before = client.get(f'/api/runs/{anchor}').json()
    assert '00899' not in {row['key'] for row in before['accepted']}
    reply = conflict(client, anchor, 35)
    assert reply.status_code == 200
    report = reply.json()['report']
    chosen = next(row for row in report['accepted'] if row['key'] == '00899')
    assert chosen['line'] == 35 and chosen['amount'] == '240.00'
    assert dict((item['metric'], item['value']) for item in chosen['proof'])['合格株数'] == '1'
    dropped = next(row for row in report['suppressed']
                   if row['key'] == '00899' and row['code'] == 'ADOPTED_SOURCE')
    assert dropped['line'] == 36
    assert not [row for row in report['quarantine'] if row['key'] == '00899']


def test_ruling_is_written_once_to_the_review_ledger(client, anchor):
    first = conflict(client, anchor, 35).json()['entry']
    retry = client.post(f'/api/adjudicate/{anchor}', json={
        'key': '00899', 'revision': 2, 'line': 35, 'digest': first['digest'],
        'note': '采信巡检卡签字的那份',
    })
    assert retry.status_code == 200
    assert retry.json()['entry']['version'] == first['version']
    history = client.get(f'/api/review/{anchor}').json()
    assert [(row['kind'], row['key'], row['line']) for row in history if row['kind'] == '采信'] == \
        [('采信', '00899', 35)]


def test_competing_ruling_cannot_take_effect(client, anchor):
    assert conflict(client, anchor, 35).status_code == 200
    rival = conflict(client, anchor, 36)
    assert (rival.status_code, rival.json()['code']) == (409, 'RULING_EXISTS')
    report = client.get(f'/api/runs/{anchor}').json()
    assert [row['line'] for row in report['accepted'] if row['key'] == '00899'] == [35]


def test_ruling_needs_note(client, anchor):
    assert conflict(client, anchor, 35, note='  ').json()['code'] == 'REVIEW_NOTE'


def test_ruling_requires_a_conflicting_key(client, anchor):
    row = source_row(client, anchor, 4, '00101')
    assert client.post(f'/api/adjudicate/{anchor}', json={
        'key': '00101', 'revision': 1, 'line': 4, 'digest': row['digest'], 'note': '无此冲突',
    }).json()['code'] == 'REVIEW_DECISION'


def test_adopting_the_other_source_flips_the_count(client, anchor):
    report = conflict(client, anchor, 36).json()['report']
    chosen = next(row for row in report['accepted'] if row['key'] == '00899')
    assert chosen['line'] == 36 and chosen['amount'] == '210.00'


def test_two_reviewers_only_one_ruling_lands(client, anchor):
    rows = {row['line']: row for row in client.get(f'/api/runs/{anchor}').json()['quarantine']
            if row['key'] == '00899'}

    def submit(line):
        return client.post(f'/api/adjudicate/{anchor}', json={
            'key': '00899', 'revision': 2, 'line': line, 'digest': rows[line]['digest'], 'note': '并发裁决',
        })

    with ThreadPoolExecutor(max_workers=2) as pool:
        codes = sorted(pool.map(lambda line: submit(line).status_code, (35, 36)))
    assert codes == [200, 409]
    report = client.get(f'/api/runs/{anchor}').json()
    assert len([row for row in report['accepted'] if row['key'] == '00899']) == 1
    assert len([row for row in client.get(f'/api/review/{anchor}').json()
                if row['kind'] == '采信']) == 1


def test_same_ruling_retried_in_parallel_is_written_once(client, anchor):
    row = next(item for item in client.get(f'/api/runs/{anchor}').json()['quarantine']
               if item['key'] == '00899' and item['line'] == 35)

    def submit(_):
        return client.post(f'/api/adjudicate/{anchor}', json={
            'key': '00899', 'revision': 2, 'line': 35, 'digest': row['digest'], 'note': '并发重试',
        })

    with ThreadPoolExecutor(max_workers=4) as pool:
        responses = list(pool.map(submit, range(4)))
    assert {item.status_code for item in responses} == {200}
    history = [item for item in client.get(f'/api/review/{anchor}').json() if item['kind'] == '采信']
    assert len(history) == 1


def test_concurrent_review_verdicts_leave_one_winner(client, anchor):
    def submit(_):
        return client.post(f'/api/review/{anchor}',
                           json={'version': 0, 'decision': '确认', 'note': '并发复核'})

    with ThreadPoolExecutor(max_workers=4) as pool:
        statuses = sorted(item.status_code for item in pool.map(submit, range(4)))
    assert statuses.count(200) == 1 and statuses.count(409) == 3
    assert len(client.get(f'/api/review/{anchor}').json()) == 1


def test_higher_revision_voids_the_old_ruling(client, anchor, source):
    assert conflict(client, anchor, 35).status_code == 200
    rows = [row for row in csv.reader(io.StringIO(source.decode('utf-8-sig'))) if len(row) == 8]
    header, body = rows[0], rows[1:]
    stream = io.StringIO(newline='')
    writer = csv.writer(stream)
    writer.writerow(header)
    writer.writerows(body)
    # Revision 3 arrives for the same 街段验收单 with its own field conflict.
    base = next(row for row in body if row[0] == '00101').copy()
    first = base.copy(); first[0], first[1] = '00899', '3'
    second = base.copy(); second[0], second[1] = '00899', '3'
    second[header.index('验收日')] = '2026-10-23'
    second[header.index('观察期天数')] = '10'
    second[header.index('单株款元')] = '210'
    second[header.index('逐株事件')] = '桂花:2026-09-01:种植;桂花:2026-09-15:死亡;桂花:2026-10-01:补植;桂花:2026-10-11:巡检存活'
    writer.writerow(first); writer.writerow(second)
    fresh = client.post('/api/runs', json={'data': stream.getvalue()}).json()
    # The revision-2 ruling names a source that no longer leads, so it lapses
    # and the revision-3 conflict is isolated again instead of being paid.
    assert fresh['manifest']['run_id'] != anchor
    assert '00899' not in {row['key'] for row in fresh['accepted']}
    assert {row['revision'] for row in fresh['quarantine'] if row['key'] == '00899'} == {3}
