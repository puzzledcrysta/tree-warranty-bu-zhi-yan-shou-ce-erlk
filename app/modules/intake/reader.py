import csv
from io import StringIO
from app.errors import DataError


def decode(payload):
    for encoding in ('utf-8-sig','gb18030'):
        try:
            return payload.decode(encoding), encoding
        except UnicodeDecodeError:
            continue
    raise DataError('ENCODING','只接受 UTF-8 或 GB18030')


def records(text):
    reader = csv.reader(StringIO(text, newline=''),strict=True)
    try:
        while True:
            line = reader.line_num + 1
            yield line, next(reader)
    except StopIteration:
        return
    except csv.Error as error:
        raise DataError('CSV',f'第 {reader.line_num} 行表格语法错误') from error
