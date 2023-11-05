import pathlib

from .views import index,reports,load_reports

PROJECT_ROOT = pathlib.Path(__file__).parent


def setup_routes(app):
    app.router.add_get('/', index)
    app.router.add_get('/{org}', reports, name='reports')
    app.router.add_post('/{org}', load_reports, name='load_reports')