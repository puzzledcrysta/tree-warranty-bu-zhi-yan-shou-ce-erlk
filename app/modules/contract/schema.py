from app.settings import KEY, FIELDS
from app.errors import DataError

REQUIRED = (KEY,'修订号','提交时间',*FIELDS)
ALIASES = {'业务编号':KEY,'版本':'修订号','更新时刻':'提交时间','备注':'原始备注'}
MISSING = {'','-','n/a','null','未知'}


def mapping(header):
    names = [ALIASES.get(name,name) for name in header]
    if len(set(names)) != len(names) or set(REQUIRED)-set(names):
        raise DataError('CONTRACT','必需字段缺失或新旧字段重复')
    return names
