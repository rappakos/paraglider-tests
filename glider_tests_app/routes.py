from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from . import views

router = APIRouter()

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