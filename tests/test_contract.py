import pytest
from app.errors import DataError
from app.modules.contract.service import normalize
from app.modules.intake.service import intake
from app.settings import KEY


def converted(source):
    return normalize(intake(source))


def test_missing(source):
    # TRAP-07
    assert {item['key'] for item in converted(source)[1] if item['code']=='REQUIRED'} == {'00898'}


def test_leading_zero(source):
    # TRAP-08
    assert converted(source)[0][0]['key'] == '00101'


def test_offsets(source):
    # TRAP-11
    rows,_ = converted(source)
    assert rows[0]['time'] == rows[1]['time'] == '2026-11-18T01:30:00+00:00'


def test_legacy_aliased():
    # TRAP-17
    from pathlib import Path
    payload = (Path(__file__).resolve().parents[1] / 'sample_data/legacy.csv').read_bytes()
    row, = converted(payload)[0]
    assert row['key'] == '00013' and row['revision']==1


def test_fullwidth_version(sample_csv):
    row, = converted(sample_csv({'修订号':'２'}))[0]
    assert row['revision']==2


def test_no_naive_local_clock(sample_csv):
    _,bad = converted(sample_csv({'提交时间':'2026-11-18T10:00:00'}))
    assert [row['code'] for row in bad] == ['TIMESTAMP']


def test_unknown_columns_are_not_required_substitutes():
    with pytest.raises(DataError) as error:
        converted(b'foo,bar\n1,2')
    assert error.value.code == 'CONTRACT'
