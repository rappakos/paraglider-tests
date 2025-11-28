# middlewares.py
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.exceptions import RequestValidationError


async def handle_404(request: Request, exc: Exception) -> HTMLResponse:
    templates = request.app.state.templates
    return templates.TemplateResponse(request, "404.html", {"request": request}, status_code=404)


async def handle_500(request: Request, exc: Exception) -> HTMLResponse:
    templates = request.app.state.templates
    return templates.TemplateResponse(request, "500.html", {"request": request}, status_code=500)


def setup_middlewares(app: FastAPI):
    """Setup FastAPI exception handlers for 404 and 500 errors."""
    
    @app.exception_handler(404)
    async def not_found_handler(request: Request, exc: Exception):
        return await handle_404(request, exc)

    @app.exception_handler(500)
    async def server_error_handler(request: Request, exc: Exception):
        return await handle_500(request, exc)