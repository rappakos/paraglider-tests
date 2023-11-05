# views.py
import os
import aiohttp_jinja2
from aiohttp import web

#from . import db

ORGS = { 
    'air-turquoise':  {'name':'Air Turquoise'},
    'dhv': {'name': 'DHV'}
}

def redirect(router, route_name):
    location = router[route_name].url_for()
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
            'org': ORGS[org]            
        }
    else:
         raise web.HTTPNotFound(reason="Organization not available")