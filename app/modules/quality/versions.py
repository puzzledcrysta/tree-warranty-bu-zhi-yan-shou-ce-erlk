from collections import defaultdict
from app.evidence import finding


def split_versions(records, unverified):
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
            conflicts.extend(finding(row,'REV_CONFLICT',f'最高修订 {latest} 的来源字段互相冲突') for row in candidates)
        else:
            ready.append(candidates[0])
            duplicates.extend(finding(row,'EXACT_DUP',f'同为修订 {latest}，保留第 {candidates[0]["line"]} 行')
                              for row in candidates[1:])
    return ready,duplicates,conflicts
