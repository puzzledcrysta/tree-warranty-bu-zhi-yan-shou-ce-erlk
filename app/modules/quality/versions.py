from collections import defaultdict
from app.evidence import finding

ADOPTED = 'ADOPTED_SOURCE'


def split_versions(records, unverified, adopted=None):
    groups = defaultdict(list)
    for record in records:
        groups[record['key']].append(record)
    ready, duplicates, conflicts = [], [], []
    for key, group in sorted(groups.items()):
        latest = max(row['revision'] for row in group)
        pending = unverified.get(key, 0)
        if pending >= latest:
            conflicts.extend(finding(row,'REV_BLOCKED',f'修订 {pending} 仍有来源未采信') for row in group)
            continue
        candidates = sorted((row for row in group if row['revision']==latest),key=lambda row:row['line'])
        older = [row for row in group if row['revision']!=latest]
        duplicates.extend(finding(row,'SUPERSEDED',f'修订 {latest} 取代旧版本') for row in older)
        signatures = {tuple(row['fields'].items()) for row in candidates}
        if len(signatures)>1:
            picked = adopt(candidates,adopted.get(key))
            if picked is None:
                conflicts.extend(finding(row,'REV_CONFLICT',f'最高修订 {latest} 的来源字段互相冲突') for row in candidates)
                continue
            ready.append(picked)
            duplicates.extend(finding(row,ADOPTED,
                                      f'采信第 {picked["line"]} 行原始底单，修订 {latest} 的其余来源不再参与复算')
                              for row in candidates if row is not picked)
        else:
            ready.append(candidates[0])
            duplicates.extend(finding(row,'EXACT_DUP',f'同为修订 {latest}，保留第 {candidates[0]["line"]} 行')
                              for row in candidates[1:])
    return ready,duplicates,conflicts


def adopt(candidates, decision):
    """Return the chosen source row for a conflicting same-revision key.

    A ruling only applies while it still names a live candidate at the
    revision it was made for; once a higher revision arrives the old ruling
    stops matching and the conflict resurfaces.
    """
    if not decision:
        return None
    chosen = [row for row in candidates if row['revision']==decision['revision']
              and row['line']==decision['line'] and row.get('digest')==decision['digest']]
    return chosen[0] if len(chosen)==1 else None
