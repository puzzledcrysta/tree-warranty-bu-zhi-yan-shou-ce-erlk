from app.errors import DataError
from app.evidence import finding
from app.settings import KEY, FIELDS
from app.modules.domain.values import whole, instant
from .schema import mapping, REQUIRED, MISSING


def normalize(source):
    names = mapping(source['header'])
    passed, rejected = [], list(source['rejected'])
    for record in source['rows']:
        values = dict(zip(names,record['values']))
        key = values[KEY]
        revision = None
        try:
            if not any(values[k].casefold() in MISSING for k in (KEY,'修订号')):
                revision = whole(values['修订号'],1,10**9)
            if any(values[k].casefold() in MISSING for k in REQUIRED):
                raise DataError('REQUIRED','主键、修订号、时间和业务字段均须填写')
            changed = instant(values['提交时间']).isoformat()
        except DataError as error:
            issue = finding(dict(record,key=key),error.code,str(error))
            if revision is not None:
                issue['revision'] = revision
            rejected.append(issue)
            continue
        passed.append({'key':key,'revision':revision,'time':changed,'line':record['line'],
                       'raw':record['raw'],'fields':{field:values[field] for field in FIELDS},
                       'note':values.get('原始备注','')})
    return passed, rejected
