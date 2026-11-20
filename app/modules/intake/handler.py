from fastapi import APIRouter, Response
from app.inputs import Source, read_sample
from .service import intake

router = APIRouter()

@router.post('/api/intake')
def inspect_file(source: Source):
    return intake(source.raw())

@router.get('/api/samples/{name}')
def sample(name: str):
    return Response(read_sample(name),media_type='text/csv; charset=utf-8')
