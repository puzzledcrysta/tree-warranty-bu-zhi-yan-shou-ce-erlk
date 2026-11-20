from decimal import Decimal
import pytest
from app.errors import DataError
from app.modules.domain.rule import evaluate


def test_replant_resets(cases):
    # TRAP-114
    actual, proof = evaluate(cases['replant_resets'])
    assert actual == Decimal('240.00')
    assert Decimal(str(dict((label, value) for label, value, _ in proof)['合格株数'])) == Decimal('1')


def test_mature_replant(cases):
    actual, proof = evaluate(cases['mature_replant'])
    assert actual == Decimal('210.00')
    assert Decimal(str(dict((label, value) for label, value, _ in proof)['合格株数'])) == Decimal('1')


def test_survival_only_early(cases):
    actual, proof = evaluate(cases['survival_only_early'])
    assert actual == Decimal('0.00')
    assert Decimal(str(dict((label, value) for label, value, _ in proof)['合格株数'])) == Decimal('0')


def test_future_ignored(cases):
    actual, proof = evaluate(cases['future_ignored'])
    assert actual == Decimal('100.00')
    assert Decimal(str(dict((label, value) for label, value, _ in proof)['合格株数'])) == Decimal('1')


def test_same_reading(cases):
    actual, proof = evaluate(cases['same_reading'])
    assert actual == Decimal('120.00')
    assert proof


def test_unreplaced(cases):
    actual, proof = evaluate(cases['unreplaced'])
    assert actual == Decimal('0.00')
    assert proof


def test_replant_active(cases):
    with pytest.raises(DataError) as error:
        evaluate(cases['replant_active'])
    assert error.value.code == 'TREE_SEQUENCE'


def test_conflicting_date(cases):
    # TRAP-14
    with pytest.raises(DataError) as error:
        evaluate(cases['conflicting_date'])
    assert error.value.code == 'TREE_CONFLICT'


def test_unanchored(cases):
    with pytest.raises(DataError) as error:
        evaluate(cases['unanchored'])
    assert error.value.code == 'TREE_SEQUENCE'
