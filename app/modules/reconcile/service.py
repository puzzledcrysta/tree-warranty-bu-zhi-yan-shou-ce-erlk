from decimal import Decimal
from .ledger import ledger


def compare(accepted,payload):
    expected = ledger(payload)
    actual = {row['key']:(Decimal(row['amount']),row['line']) for row in accepted}
    rows, matches = [],0
    for key in sorted(actual.keys()|expected.keys()):
        value,line = actual.get(key,(None,None))
        book,book_line = expected.get(key,(None,None))
        delta = (value or Decimal(0))-(book or Decimal(0))
        reason = ('MISSING_BOOK' if book is None else 'MISSING_RESULT' if value is None else
                  'AMOUNT_DELTA' if delta else 'MATCH')
        matches += reason=='MATCH'
        rows.append({'key':key,'amount':str(value) if value is not None else None,
                     'reference':str(book) if book is not None else None,'delta':str(delta),
                     'line':line,'book_line':book_line,'code':reason})
    actual_total = sum((pair[0] for pair in actual.values()),Decimal(0))
    book_total = sum((pair[0] for pair in expected.values()),Decimal(0))
    return {'rows':rows,'matched':matches,'mismatched':len(rows)-matches,'actual':str(actual_total),
            'expected':str(book_total),'delta':str(actual_total-book_total)}
