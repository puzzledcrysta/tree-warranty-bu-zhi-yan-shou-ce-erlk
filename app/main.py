from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from app.errors import DataError
from app.settings import TITLE, ROOT
from app.web import router as web
from app.modules.intake.handler import router as intake
from app.modules.contract.handler import router as contract
from app.modules.quality.handler import router as quality
from app.modules.domain.handler import router as domain
from app.modules.reconcile.handler import router as reconcile
from app.modules.runs.handler import router as runs
from app.modules.review.handler import router as review

app = FastAPI(title=TITLE, docs_url=None, redoc_url=None)
app.mount('/static',StaticFiles(directory=ROOT/'app/static'),name='static')
for router in (web,intake,contract,quality,domain,reconcile,runs,review):
    app.include_router(router)

@app.exception_handler(DataError)
def data_error(_: Request, error: DataError):
    return JSONResponse({'code':error.code,'detail':str(error)},status_code=error.status)

@app.get('/health')
def health():
    return {'status':'ok'}
