from app.evidence import distribution
from .versions import split_versions


def inspect(records, rejected):
    unverified = {}
    for row in rejected:
        if 'revision' in row:
            key, revision = row['key'], row['revision']
            unverified[key] = max(revision, unverified.get(key, 0))
    ready, duplicates, conflicts = split_versions(records, unverified)
    quarantine = sorted([*rejected,*conflicts],key=lambda row:row['line'])
    return {'ready':ready,'suppressed':sorted(duplicates,key=lambda row:row['line']),
            'rejected':quarantine,'reasons':distribution(quarantine)}
