import csv
from decimal import Decimal
from io import StringIO
import pytest
from app.errors import DataError
from app.pipeline import execute
from app.modules.reconcile.service import compare
from app.settings import KEY, UNIT


def test_input_rows_conserved(source,book):
    result = execute(source,book)
    assert result['balanced'] is True
    assert [row['key'] for row in result['quarantine'] if row['key'].startswith('009')] == ['00901','00902']
    assert result['counts'] == {'input':36,'accepted':26,'rejected':6,'suppressed':2,'blank':1,'repeated_header':1}


def test_reference_discrepancies_are_distinguished(source,book):
    by_key = {row['key']:row for row in execute(source,book)['book']['rows']}
    assert [(by_key[key]['code'],Decimal(by_key[key]['delta'])) for key in ('00102','09999')] == [('AMOUNT_DELTA',Decimal('-1')),('MISSING_RESULT',Decimal('-7'))]


def test_missing_book(source,book):
    row, = [row for row in execute(source,book)['book']['rows'] if row['key']=='00103']
    assert row['reference'] is None and row['code']=='MISSING_BOOK'


def test_total_agrees_with_key_deltas(source,book):
    result = execute(source,book)['book']
    assert result['matched']==24 and result['mismatched']==3
    assert Decimal(result['delta']) == sum(Decimal(row['delta']) for row in result['rows'])


def test_duplicate_reference_rejected(source,book):
    rows = list(csv.reader(StringIO(book.decode())))
    out = StringIO(newline='')
    csv.writer(out).writerows([*rows,rows[1]])
    with pytest.raises(DataError) as error:
        execute(source,out.getvalue().encode())
    assert error.value.code == 'BOOK_CONFLICT'


def test_zero_and_absent_differ():
    result = compare([{'key':'009','line':2,'amount':'0'}],f'{KEY},外部记录值({UNIT})\n'.encode())
    assert result['rows'][0]['code']=='MISSING_BOOK' and result['delta']=='0'
