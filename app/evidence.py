from collections import Counter


def finding(record, code, detail):
    return {'line': record['line'], 'key': record.get('key', ''), 'raw': record['raw'],
            'code': code, 'detail': detail}


def distribution(findings):
    return dict(sorted(Counter(item['code'] for item in findings).items()))
