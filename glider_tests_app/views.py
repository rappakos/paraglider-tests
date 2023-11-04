# views.py
import os
import aiohttp_jinja2
from aiohttp import web

#from . import db


def redirect(router, route_name):
    location = router[route_name].url_for()
    return web.HTTPFound(location)

@aiohttp_jinja2.template('index.html')
async def index(request):
    
    return {
            'test': 'ok'
    }
