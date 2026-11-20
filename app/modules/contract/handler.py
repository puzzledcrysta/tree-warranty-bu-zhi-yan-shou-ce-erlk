from fastapi import APIRouter
from app.inputs import Source
from app.modules.intake.service import intake
from .service import normalize
from .schema import REQUIRED, ALIASES

router = APIRouter()

@router.get('/api/contract')
def fields():
    return {'required':REQUIRED,'aliases':ALIASES}

@router.post('/api/contract')
def apply(source: Source):
    accepted,rejected = normalize(intake(source.raw()))
    return {'accepted':accepted,'rejected':rejected}
