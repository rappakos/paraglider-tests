import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from config import DefaultConfig

from glider_tests_app.routes import router
from glider_tests_app.middlewares import setup_middlewares

CONFIG = DefaultConfig()

app = FastAPI(title="paraglider-tests")

# Templates available to views via request.app.state.templates
templates = Jinja2Templates(directory="glider_tests_app/templates")
app.state.templates = templates

# Serve static files (if present)
try:
    app.mount("/static", StaticFiles(directory="glider_tests_app/static"), name="static")
except Exception:
    # Directory may be missing in some setups; swallow to avoid startup crash
    pass

# Include application routes
app.include_router(router)

# Apply project middlewares (CORS, error handlers, etc.)
setup_middlewares(app)


if __name__ == "__main__":
    uvicorn.run("main:app", host="127.0.0.1", port=CONFIG.PORT, reload=True)
