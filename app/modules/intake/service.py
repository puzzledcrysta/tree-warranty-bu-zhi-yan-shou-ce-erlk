from app.errors import DataError
from app.evidence import finding
from .reader import decode, records


def intake(payload):
    text, encoding = decode(payload)
    if not text:
        raise DataError('EMPTY','文件无内容')
    if not text.strip():
        raise DataError('BLANK_FILE','文件只有空白')
    header = None
    rejected, accepted, blanks, repeat = [],[],[],[]
    for line, raw in records(text):
        values = [part.strip().removeprefix('\ufeff') for part in raw]
        if header is None:
            if not any(values):
                continue
            header = values
            if not all(header) or len(set(header)) != len(header):
                raise DataError('HEADER','表头存在空列或重复字段')
            continue
        if not any(values):
            blanks.append(line)
        elif values == header:
            repeat.append(line)
        elif len(values) != len(header):
            rejected.append(finding({'line':line,'raw':raw}, 'WIDTH', f'{len(values)} 列，应为 {len(header)} 列'))
        else:
            accepted.append({'line':line,'raw':raw,'values':values})
    if header is None:
        raise DataError('BLANK_FILE','文件只有空白')
    count = sum(map(len,(rejected, accepted, blanks, repeat)))
    if not count:
        raise DataError('HEADER_ONLY','文件只有表头')
    return {'header':header,'encoding':encoding,'rows':accepted,'rejected':rejected,'blank_lines':blanks,
            'header_lines':repeat,'input_count':count}
