from fastapi import APIRouter
from app.inputs import Paired
from app.modules.review.decisions import decisions
from app.pipeline import execute

router = APIRouter()

@router.post('/api/reconcile')
def reconcile(source: Paired):
    report = execute(source.raw(),source.ledger(),decisions())
    return {key:report[key] for key in ('book','counts','balanced')}
