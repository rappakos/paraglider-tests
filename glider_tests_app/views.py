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
    
    return {
            'test': 'ok'
    }

@aiohttp_jinja2.template('testdata.html')
async def testdata(request):
    org = request.match_info.get('org', None)
    if org in ORGS:
        return {
            'org': org,
            'orgdata': ORGS[org]            
        }
    else:
         raise web.HTTPNotFound(reason="Organization not available")
    
async def load_tests(request):
    org = request.match_info.get('org', None)    
    if request.method == 'POST':

        start_date = await db.get_start_date(org)
        print(start_date)
        if org=='air-turquoise':
            pages = await airturquoise_loader.get_tests(start_date)
            print(len(pages))


        raise redirect(request.app.router, 'testdata', org=org)
    else:
        raise NotImplementedError("invalid?")        