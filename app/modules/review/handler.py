from fastapi import APIRouter, Response
from app.inputs import Adoption, Review
from .bundle import bundle
from .decisions import adopt, decide, timeline

router = APIRouter()

@router.get('/api/review/{run_id}')
def reviews(run_id: str):
    return timeline(run_id)

@router.post('/api/review/{run_id}')
def commit(run_id: str, review: Review):
    return decide(run_id,review.version,review.decision,review.note)

@router.post('/api/adjudicate/{run_id}')
def adjudicate(run_id: str, choice: Adoption):
    entry, report = adopt(run_id,choice)
    return {'entry':entry,'report':report}

@router.get('/api/export/{run_id}')
def export(run_id: str):
    return Response(bundle(run_id),media_type='application/json',
                    headers={'Content-Disposition':f'attachment; filename="evidence-{run_id}.json"'})
