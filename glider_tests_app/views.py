# views.py
import os
import aiohttp_jinja2
from aiohttp import web

from . import db
from . import airturquoise_loader

ORGS = { 
    'air-turquoise':  {'name':'Air Turquoise'},
    'dhv': {'name': 'DHV'}
}

def redirect(router, route_name, org = None):
    location = router[route_name].url_for(org=org)
    return web.HTTPFound(location)

@aiohttp_jinja2.template('index.html')
async def index(request):    
    return {'data': (await db.get_stats()).to_dict('records')}

@aiohttp_jinja2.template('testdata.html')
async def testdata(request):
    org = request.match_info.get('org', None)
    if org in ORGS:
        #for classification in ['B','C']:
        #    start_date = await db.get_start_date(org,classification)
        #    print(classification,start_date)
        reports = await db.get_reports(org)
        #print(reports.head())

        return {
            'org': org,
            'orgdata': ORGS[org],            
            'reports': reports.to_dict('records')
        }
    else:
         raise web.HTTPNotFound(reason="Organization not available")
    
async def load_tests(request):
    org = request.match_info.get('org', None)    
    if request.method == 'POST':
        if org=='air-turquoise':
            for classification in ['B','C']:
                start_date = await db.get_start_date(org,classification)
                print(classification,start_date)

                pages = await airturquoise_loader.get_tests(classification,start_date)
                for page in pages:
                    await db.save_tests(org, page)

        raise redirect(request.app.router, 'testdata', org=org)
    else:
        raise NotImplementedError("invalid?")        