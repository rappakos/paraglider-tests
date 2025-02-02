import pathlib

from .views import index,reports,load_reports,load_details,load_pdf,item_details,evaluations,load_eval

PROJECT_ROOT = pathlib.Path(__file__).parent


def setup_routes(app):
    app.router.add_get('/', index)
    app.router.add_get('/{org}', reports, name='reports')
    app.router.add_post('/{org}', load_reports, name='load_reports')
    app.router.add_post('/{org}/details', load_details, name='load_details')
    app.router.add_post('/{org}/load-pdf', load_pdf, name='load_pdf')
    app.router.add_post('/{org}/load-eval', load_eval, name='load_eval')
    # air turquoise old => item_link - "/reports/items"
    # air turquoise new ???
    # dhv => item name 
    app.router.add_get('/{org}/items/{item_id}', item_details, name='item_details')
    app.router.add_get('/{org}/evaluations', evaluations, name='evaluations')