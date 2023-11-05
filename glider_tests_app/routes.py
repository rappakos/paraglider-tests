import pathlib

from .views import index,reports,load_reports,load_details,load_pdf

PROJECT_ROOT = pathlib.Path(__file__).parent


def setup_routes(app):
    app.router.add_get('/', index)
    app.router.add_get('/{org}', reports, name='reports')
    app.router.add_post('/{org}', load_reports, name='load_reports')
    app.router.add_post('/{org}/details', load_details, name='load_details')
    app.router.add_post('/{org}/load-pdf', load_pdf, name='load_pdf')