import pathlib

from .views import index,testdata

PROJECT_ROOT = pathlib.Path(__file__).parent


def setup_routes(app):
    app.router.add_get('/', index)
    app.router.add_get('/{org}', testdata, name='testdata')