from collections import defaultdict
from datetime import timedelta
from decimal import Decimal as D, ROUND_HALF_UP
from app.errors import DataError
from .values import calendar, whole, number, parts


def evaluate(row):
    cutoff = calendar(row['验收日'])
    period = whole(row['观察期天数'],1,730)
    price = number(row['单株款元'],0,10**6)
    events = defaultdict(dict)
    types = {'种植','死亡','补植','巡检存活'}
    for item in parts(row['逐株事件']):
        fields = item.split(':')
        if len(fields) != 3 or not fields[0] or fields[-1] not in types:
            raise DataError('TREE_FORMAT','事件须包含树号、日期、状态')
        name, raw, state = fields
        day = calendar(raw)
        if day > cutoff:
            continue
        if day in events[name] and events[name][day] != state:
            raise DataError('TREE_CONFLICT', f'{name} 在 {day} 有矛盾状态')
        events[name][day] = state
    if not events:
        raise DataError('TREE_NO_EVENTS','验收日之前没有逐株记录')
    paid, proof = 0, []
    for name, timeline in sorted(events.items()):
        active, planted, verified = False, None, False
        for day, state in sorted(timeline.items()):
            if state=='种植' and planted is None or state=='补植' and planted is not None and not active:
                active, planted, verified = True, day, False
            elif state=='死亡' and active:
                active, verified = False, False
            elif state=='巡检存活' and active:
                verified |= (day-planted).days >= period
            else:
                raise DataError('TREE_SEQUENCE', f'{name} 在 {day} 的{state}事件无法接续')
        accepted = active and verified
        paid += accepted
        status = '验收通过' if accepted else '观察期未满' if active and (cutoff-planted).days<period else '需补巡检' if active else '待补植'
        proof.append((f'{name} · {planted}',status,''))
    proof.append(('合格株数',paid,'株'))
    return (price*paid).quantize(D('0.01'),rounding=ROUND_HALF_UP), proof
