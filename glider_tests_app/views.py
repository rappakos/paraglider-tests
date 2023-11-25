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

DOWNLOAD_FOLDER = 'data/pdf'

def redirect(router, route_name, org = None):
    location = router[route_name].url_for(org=org)
    return web.HTTPFound(location)

@aiohttp_jinja2.template('index.html')
async def index(request):    
    return {'data': (await db.get_stats()).to_dict('records')}

@aiohttp_jinja2.template('reports.html')
async def reports(request):
    from os.path import exists

    org = request.match_info.get('org', None)
    if org in ORGS:
        reports = await db.get_reports(org)

        if not reports.empty:
            reports['pdf_available'] = reports.apply(lambda row: exists(f"{DOWNLOAD_FOLDER}/{'_'.join(row.item_name.split())}.pdf") , axis=1)
            #reports['eval_available'] = reports.apply(lambda x: True if x.evaluation==1 else False , axis=1)

        evaluations = await db.get_evaluations(org)
        print(evaluations.head())

        return {
            'org': org,
            'orgdata': ORGS[org],            
            'reports': reports.to_dict('records')
        }
    else:
         raise web.HTTPNotFound(reason="Organization not available")

@aiohttp_jinja2.template('item_details.html')
async def item_details(request):
    org, item_id = request.match_info.get('org', None), request.match_info.get('item_id', None)

    if org in ORGS:
        report = await db.get_report_details(org, item_id)
        #print(report.head())
        textrows = []
        if not report.empty:
            for item in report.itertuples(index=None):
                evaluation = await db.get_evaluation(org, item.item_name)
                print(evaluation)
                if not evaluation.empty:
                    print('from db')
                    #print(evaluation.head())
                    textrows = [f"{e.test}: {e.rating}" for e in evaluation.itertuples(index=None)]
                else:
                    fname = f"{DOWNLOAD_FOLDER}/{'_'.join(item.item_name.split())}.pdf"
                    #print(fname)
                    evaluation = await airturquoise_loader.extract_pdf_data(item.item_name, fname)
                    print('from pdf')          
                    #print(evaluation.head())
                    if evaluation is not None:
                        textrows = [f"{e.test}: {e.rating}" for e in evaluation.itertuples(index=None)]
                        await db.save_evaluation(org, evaluation)
                    
        return {
            'id': item_id,
            'report': report.to_dict('records')[0],
            'text': textrows
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
                    await db.save_download_link(item.report_link, download_link)
                else:
                    print(f'no success - {airturquoise_loader.AIR_TURQUISE_BASE_URL}{item.report_link}')


        raise redirect(request.app.router, 'reports', org=org)
    else:
        raise NotImplementedError("invalid?")            
    
async def load_pdf(request):
    import requests
    from os.path import exists

    org = request.match_info.get('org', None)    
    if request.method == 'POST':
        if org=='air-turquoise':
            file_checks =  await db.get_download_links(org)
            for item in file_checks.itertuples(index=None):
                #print(item.item_name, item.download_link)
                fname = f"{DOWNLOAD_FOLDER}/{'_'.join(item.item_name.split())}.pdf"
                if exists(fname):
                    print(f'{fname} - ok')
                else:
                    url = f"{airturquoise_loader.AIR_TURQUISE_BASE_URL}{item.download_link}"
                    print(f'downloading {fname} from {url}')
                    r = requests.get(url, allow_redirects=True)
                    open(fname, 'wb').write(r.content)

        raise redirect(request.app.router, 'reports', org=org)
    else:
        raise NotImplementedError("invalid?")                     