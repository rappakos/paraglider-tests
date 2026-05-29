import os
from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse
from typing import Optional
from . import views
from . import db

prefix = os.environ.get("GLIDER_TESTS_APP_ROOT_PATH", "")

router = APIRouter(prefix=prefix, tags=["glider-tests"])
api_router = APIRouter(prefix=prefix + "/api", tags=["glider-tests-api"])

@router.get("/", response_class=HTMLResponse)
async def index_route(request: Request):
    return await views.index(request)

@router.get("/{org}", response_class=HTMLResponse, name="reports")
async def reports_route(request: Request, org: str):
    return await views.reports(org, request)

@router.post("/{org}", response_class=HTMLResponse)
async def load_reports_route(request: Request, org: str):
    return await views.load_reports(org, request)

@router.post("/{org}/details", response_class=HTMLResponse)
async def load_details_route(request: Request, org: str):
    return await views.load_details(org, request)

@router.post("/{org}/load-pdf", response_class=HTMLResponse)
async def load_pdf_route(request: Request, org: str):
    return await views.load_pdf(org, request)

@router.post("/{org}/load-eval", response_class=HTMLResponse)
async def load_eval_route(request: Request, org: str):
    return await views.load_eval(org, request)

@router.get("/{org}/items/{item_id}", response_class=HTMLResponse, name="item_details")
async def item_details_route(request: Request, org: str, item_id: str):
    return await views.item_details(org, item_id, request)

@router.get("/{org}/evaluations", response_class=HTMLResponse, name="evaluations")
async def evaluations_route(request: Request, org: str):
    return await views.evaluations(org, request)


# JSON API endpoints

@api_router.get("/search")
async def api_search_wings(
    q: str = Query(..., description="Comma-separated glider name search strings"),
    weight: Optional[int] = Query(None, description="Takeoff weight in kg"),
    classification: Optional[str] = Query(None, description="Glider class filter: A, B, C, D (comma-separated)")
):
    """Search and compare paraglider certification test results."""
    results = await db.get_evaluations(
        org='all',
        item_name=q,
        weight=str(weight) if weight else '',
        classification=classification or ''
    )
    if results.empty:
        return JSONResponse(content={"results": [], "query": {"q": q, "weight": weight, "classification": classification}})

    return JSONResponse(content={
        "results": results.to_dict('records'),
        "query": {"q": q, "weight": weight, "classification": classification}
    })