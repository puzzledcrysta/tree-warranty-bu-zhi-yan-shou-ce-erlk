from app.evidence import distribution
from app.modules.intake.service import intake
from app.modules.contract.service import normalize
from app.modules.quality.service import inspect
from app.modules.domain.service import calculate
from app.modules.reconcile.service import compare


def stages(source,adopted=None):
    raw = intake(source)
    contract, rejected = normalize(raw)
    quality = inspect(contract,rejected,adopted)
    accepted, domain_bad = calculate(quality['ready'])
    bad = sorted([*quality['rejected'],*domain_bad],key=lambda row:row['line'])
    return {'intake':raw,'contract':contract,'quality':quality,'accepted':accepted,
            'domain_bad':domain_bad,'rejected':bad}


def tally(result):
    raw, accepted, bad = (result[key] for key in ('intake','accepted','rejected'))
    suppressed = result['quality']['suppressed']
    counts = {'input':raw['input_count'],'accepted':len(accepted),'rejected':len(bad),
              'suppressed':len(suppressed),'blank':len(raw['blank_lines']),'repeated_header':len(raw['header_lines'])}
    balanced = counts['input'] == sum(value for key,value in counts.items() if key!='input')
    if not balanced:
        raise RuntimeError('来源记录数量无法闭合')
    return counts,balanced


def execute(source,book,adopted=None):
    result = stages(source,adopted)
    counts, balanced = tally(result)
    bad = result['rejected']
    return {'counts':counts,'balanced':balanced,'accepted':result['accepted'],'quarantine':bad,
            'suppressed':result['quality']['suppressed'],'reasons':distribution(bad),
            'book':compare(result['accepted'],book),'encoding':result['intake']['encoding']}
