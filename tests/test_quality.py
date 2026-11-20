from app.modules.contract.service import normalize
from app.modules.intake.service import intake
from app.modules.quality.service import inspect


def report(source):
    return inspect(*normalize(intake(source)))


def test_conflicting(source):
    # TRAP-14
    result = report(source)
    assert '00899' not in {row['key'] for row in result['ready']}
    assert [row['code'] for row in result['rejected'] if row['key']=='00899'] == ['REV_CONFLICT','REV_CONFLICT']


def test_redundant_transmission(source):
    taken = report(source)['suppressed']
    assert [(row['key'],row['code']) for row in taken if row['code']=='EXACT_DUP'] == [('00101','EXACT_DUP')]


def test_prefers_high_revision(source):
    row, = [row for row in report(source)['ready'] if row['key']=='00102']
    assert row['revision']==2


def test_older_is_explained(source):
    assert [row['key'] for row in report(source)['suppressed'] if row['code']=='SUPERSEDED'] == ['00102']


def test_reason_counts(source):
    codes = report(source)['reasons']
    assert codes == {'REQUIRED':1,'REV_CONFLICT':2,'WIDTH':1}


def test_earliest_evidence_retained_for_duplicates(source):
    chosen = next(row for row in report(source)['ready'] if row['key']=='00101')
    assert chosen['line'] == 2
