# views.py
import os
import aiohttp_jinja2
from aiohttp import web

from . import db
from . import airturquoise_loader
from . import dhv_loader

ORGS = { 
    'air-turquoise':  {'name':'Air Turquoise'},
    'dhv': {'name': 'DHV'},
    'all': {'name': 'all'}
}

DOWNLOAD_FOLDER = 'data/pdf'
MIN_DATE = '2020-01-01'

def get_filename(item_name:str):
    name =item_name.replace('"','')
    return f"{DOWNLOAD_FOLDER}/{'_'.join(name.split())}.pdf"


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
            reports['pdf_available'] = reports.apply(lambda row: exists(get_filename(row.item_name)) , axis=1)
            #reports['eval_available'] = reports.apply(lambda x: True if x.evaluation==1 else False , axis=1)
            reports['item_id'] = reports.apply(lambda row: '/reports/item/' + '-'.join(row.item_name.lower().replace("/","").split(' ')) if org=='dhv' else row.report_link  , axis=1)

        #evaluations = await db.get_evaluations(org)
        #print(evaluations.head())

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
        if not report.empty and org=='air-turquoise':
            for item in report.itertuples(index=None):
                evaluation = await db.get_evaluation(org, item.item_name)
                fname = get_filename(item.item_name)
                #print(evaluation)
                if not evaluation.empty:
                    params = await airturquoise_loader.extract_param_data(item.item_name, fname)
                    print(params)
                    if params:
                        await db.save_parameters(org, params)

                    #print('from db')
                    #print(evaluation.head())
                    textrows = [f"{e.test}: {e.rating}" for e in evaluation.itertuples(index=None)]
                else:
                    evaluation = await airturquoise_loader.extract_pdf_data(item.item_name, fname)
                    #print('from pdf')          
                    #print(evaluation.head())
                    if not evaluation.empty:
                        textrows = [f"{e.test}: {e.rating}" for e in evaluation.itertuples(index=None)]
                        await db.save_evaluation(org, evaluation)
                    else:
                        print('try ocr ')
                        params, evaluation = await airturquoise_loader.extract_ocr_data(item.item_name, fname)
                        if params:
                            await db.save_parameters(org, params)
                        if not evaluation.empty:
                            textrows = [f"{e.test}: {e.rating}" for e in evaluation.itertuples(index=None)]
                            await db.save_evaluation(org, evaluation)

                #temp = await airturquoise_loader.extract_textrows(item.item_name, fname)
                #print(temp)
                    

        if not report.empty and org=='dhv':
            for item in report.itertuples(index=None): # should be only 1
                params, evaluation = await dhv_loader.extract_data(item.item_name, item.report_link)
                #print(params)
                #print(evaluation)
                if params:
                    await db.save_parameters(org, params)
                if not evaluation.empty:
                    textrows = [f"{e.test}: {e.rating}" for e in evaluation.itertuples(index=None)]
                    await db.save_evaluation(org, evaluation)                

        return {
            'id': item_id,
            'report': report.to_dict('records')[0],
            'text': textrows
        }
    else:
         raise web.HTTPNotFound(reason="Organization not available")

@aiohttp_jinja2.template('evaluations.html')
async def evaluations(request):
    import pandas as pd

    org, item_name, weight,classification = request.match_info.get('org', None),request.rel_url.query.get('item_name', ''),request.rel_url.query.get('weight', ''),request.rel_url.query.get('classification', '')
    if org in ORGS:
        evaluations = await db.get_evaluations(org, item_name, weight,classification)
        #print(evaluations.head())
        #for t in evaluations['test_name'].unique():
        #    print(t)

        # removes rows with 'weight_min','weight_max' None
        #pivoted = pd.pivot_table(evaluations,index=['item_name','weight_min','weight_max'], columns='test_name', values='test_value', aggfunc=max, fill_value=0)
        pivoted = evaluations.set_index(['item_name','report_class','weight_min','weight_max','test_name']).unstack('test_name')
        def sorter(name):
            return int(name[1].split('.')[0])

        sorted_columns = sorted(pivoted.columns.values, key=sorter)
        pivoted = pivoted[sorted_columns]
        #print(pivoted.head())

        return {
            'org': org,
            'orgdata': ORGS[org],    
            'evaluations': pivoted.to_dict('split'),
            'filter': {
                'item_name':item_name,
                'weight':weight,
                'classification':classification
            }
        }
    else:
         raise web.HTTPNotFound(reason="Organization not available")

async def load_reports(request):
    org = request.match_info.get('org', None)    
    if request.method == 'POST':
        if org in ORGS:
            # check if there are new entries
            for classification in ['A','B','C','D']:
                start_date = await db.get_start_date(org,classification)
                if start_date is None:
                    start_date = MIN_DATE
                print(classification,start_date)

                if org=='air-turquoise':
                    pages = await airturquoise_loader.get_reports(classification,start_date)
                    for page in pages:
                        await db.save_tests(org, page)
                if org=='dhv':
                    pages = await dhv_loader.get_reports(classification,start_date)
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
                fname = get_filename(item.item_name)
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
    
async def load_eval(request):
    from os.path import exists

    org = request.match_info.get('org', None)    
    if request.method == 'POST':
        if org=='air-turquoise':
            open_evals = await db.get_open_evaluations(org)
            #print(open_evals.head())
            for item in open_evals.itertuples(index=None):
                fname = get_filename(item.item_name)
                if exists(fname):
                    print('extracting', item.item_name)
                    evaluation = await airturquoise_loader.extract_pdf_data(item.item_name, fname)
                    if evaluation is not None:
                        await db.save_evaluation(org, evaluation)                    
                else:
                    print('skipping', item.item_name)

        raise redirect(request.app.router, 'reports', org=org)
    else:
        raise NotImplementedError("invalid?")         