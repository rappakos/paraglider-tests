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

@aiohttp_jinja2.template('reports.html')
async def reports(request):
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
    
async def load_reports(request):
    org = request.match_info.get('org', None)    
    if request.method == 'POST':
        if org=='air-turquoise':
            # check if there are new entries
            for classification in ['B','C']:
                start_date = await db.get_start_date(org,classification)
                print(classification,start_date)

                pages = await airturquoise_loader.get_reports(classification,start_date)
                for page in pages:
                    await db.save_tests(org, page)

        raise redirect(request.app.router, 'reports', org=org)
    else:
        raise NotImplementedError("invalid?")

async def load_details(request):
    org = request.match_info.get('org', None)    
    if request.method == 'POST':
        if org=='air-turquoise':
            open_reports = await db.get_open_reports(org)
            for item in open_reports.itertuples(index=None):
                download_link = await airturquoise_loader.get_download_link(item.report_link)
                if download_link:
                    #print(download_link)
                    await db.save_download_link(item.report_link, download_link)
                    # TODO DL PDF ?!
                else:
                    print(f'no success - {airturquoise_loader.AIR_TURQUISE_BASE_URL}{item.report_link}')


        raise redirect(request.app.router, 'reports', org=org)
    else:
        raise NotImplementedError("invalid?")            
    