import csv
import io
from app.pipeline import stages
from app.settings import FIELDS


def test_known_invalid_latest_revision_blocks_valid_old_row(source):
    reader = csv.reader(io.StringIO(source.decode('utf-8-sig')))
    header, old = next(reader), next(reader)
    new = old.copy()
    new[1] = '2'
    new[header.index(FIELDS[-1])] = 'N/A'
    stream = io.StringIO(newline='')
    csv.writer(stream).writerows([header, new, old])
    report = stages(stream.getvalue().encode())
    assert report['accepted'] == []
    assert [item['code'] for item in report['rejected']] == ['REQUIRED','REV_BLOCKED']
