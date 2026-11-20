from fastapi import APIRouter
from app.inputs import Source
from app.modules.intake.service import intake
from app.modules.contract.service import normalize
from .service import inspect

router = APIRouter()

@router.post('/api/quality')
def quality(source: Source):
    return inspect(*normalize(intake(source.raw())))
