# views.py
import os
from fastapi import Request, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse

from . import db
if True:
    from . import airturquoise_loader
if True:
    from . import dhv_loader

ORGS = { 
    'air-turquoise':  {'name':'Air Turquoise'},
    'dhv': {'name': 'DHV'},
    'all': {'name': 'all'}
}

DOWNLOAD_FOLDER = 'data/pdf'
MIN_DATE = '2020-01-01'

def get_filename(item_name:str):
    name =item_name.replace('"','').replace('/','')
    return f"{DOWNLOAD_FOLDER}/{'_'.join(name.split())}.pdf"

def generate_item_id(org,item_name,report_link ):
    from urllib.parse import parse_qs

    if org=='dhv':
        return '-'.join(item_name.lower().replace("/","").split(' '))
    if org=='air-turquoise':
        if report_link.startswith('/reports/item'):
            return report_link.replace('/reports/item/','')         
        else:
            new_id = parse_qs(report_link)['id'][0]

            return new_id+'-new'

    return None


async def index(request: Request) -> HTMLResponse:
    templates = request.app.state.templates
    stats = await db.get_stats()
    return templates.TemplateResponse("index.html", {
        "request": request,
        "data": stats.to_dict('records')
    })

async def reports(org: str, request: Request) -> HTMLResponse:
    from os.path import exists

    if org in ORGS:
        reports_df = await db.get_reports(org)

        if not reports_df.empty:
            reports_df['pdf_available'] = reports_df.apply(lambda row: exists(get_filename(row.item_name)), axis=1)
            reports_df['item_id'] = reports_df.apply(lambda row: generate_item_id(org, row.item_name, row.report_link), axis=1)

        templates = request.app.state.templates
        return templates.TemplateResponse("reports.html", {
            "request": request,
            "org": org,
            "orgdata": ORGS[org],
            "reports": reports_df.to_dict('records') if not reports_df.empty else []
        })
    else:
        raise HTTPException(status_code=404, detail="Organization not available")


async def item_details(org: str, item_id: str, request: Request) -> HTMLResponse:
    if org in ORGS:
        report = await db.get_report_details(org, item_id)
        textrows = []
        if not report.empty and org=='air-turquoise':
            for item in report.itertuples(index=None):
                evaluation = await db.get_evaluation(org, item.item_name)
                fname = get_filename(item.item_name)
                if not evaluation.empty:
                    params = await airturquoise_loader.extract_param_data(item.item_name, fname)
                    print(params)
                    if params:
                        await db.save_parameters(org, params)
                    textrows = [f"{e.test}: {e.rating}" for e in evaluation.itertuples(index=None)]
                else:
                    evaluation = await airturquoise_loader.extract_pdf_data(item.item_name, fname)
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

        if not report.empty and org=='dhv':
            for item in report.itertuples(index=None):
                params, evaluation = await dhv_loader.extract_data(item.item_name, item.report_link)
                if params:
                    await db.save_parameters(org, params)
                if not evaluation.empty:
                    textrows = [f"{e.test}: {e.rating}" for e in evaluation.itertuples(index=None)]
                    await db.save_evaluation(org, evaluation)

        templates = request.app.state.templates
        return templates.TemplateResponse("item_details.html", {
            "request": request,
            "id": item_id,
            "report": report.to_dict('records')[0],
            "text": textrows
        })
    else:
        raise HTTPException(status_code=404, detail="Organization not available")


async def evaluations(org: str, request: Request) -> HTMLResponse:
    import pandas as pd

    item_name = request.query_params.get('item_name', '')
    weight = request.query_params.get('weight', '')
    classification = request.query_params.get('classification', '')

    if org in ORGS:
        evaluations = await db.get_evaluations(org, item_name, weight, classification)

        pivoted = evaluations.set_index(['item_name','report_class','weight_min','weight_max','test_name']).unstack('test_name')
        def sorter(name):
            return int(name[1].split('.')[0])

        sorted_columns = sorted(pivoted.columns.values, key=sorter)
        pivoted = pivoted[sorted_columns]

        templates = request.app.state.templates
        return templates.TemplateResponse("evaluations.html", {
            "request": request,
            "org": org,
            "orgdata": ORGS[org],
            "evaluations": pivoted.to_dict('split'),
            "filter": {
                "item_name": item_name,
                "weight": weight,
                "classification": classification
            }
        })
    else:
        raise HTTPException(status_code=404, detail="Organization not available")


async def load_reports(org: str, request: Request) -> RedirectResponse:
    if org in ORGS:
        # check if there are new entries
        for classification in ['A','B','C','D']:
            start_date = await db.get_start_date(org, classification)
            if start_date is None:
                start_date = MIN_DATE
            print(classification, start_date)

            if org=='air-turquoise':
                pages = await airturquoise_loader.get_reports(classification, start_date)
                for page in pages:
                    await db.save_tests(org, page)
            if org=='dhv':
                pages = await dhv_loader.get_reports(classification, start_date)
                for page in pages:
                    await db.save_tests(org, page)

    return RedirectResponse(url=f"/{org}", status_code=303)


async def load_details(org: str, request: Request) -> RedirectResponse:
    if org == 'air-turquoise':
        open_reports = await db.get_open_reports(org)
        for item in open_reports.itertuples(index=None):
            download_link = await airturquoise_loader.get_download_link(item.report_link)
            if download_link:
                await db.save_download_link(item.report_link, download_link)
            else:
                print(f'no success - {airturquoise_loader.AIR_TURQUISE_BASE_URL}/reports{item.report_link}')

    return RedirectResponse(url=f"/{org}", status_code=303)            
    

async def load_pdf(org: str, request: Request) -> RedirectResponse:
    import requests
    from os.path import exists

    if org == 'air-turquoise':
        file_checks = await db.get_download_links(org)
        for item in file_checks.itertuples(index=None):
            fname = get_filename(item.item_name)
            if exists(fname):
                print(f'{fname} - ok')
            else:
                url = f"{airturquoise_loader.AIR_TURQUISE_BASE_URL}/{item.download_link}" if item.download_link.startswith('storage') else f"{airturquoise_loader.AIR_TURQUISE_BASE_URL}{item.download_link}"
                print(f'downloading {fname} from {url}')
                r = requests.get(url, allow_redirects=True)
                open(fname, 'wb').write(r.content)

    return RedirectResponse(url=f"/{org}", status_code=303)                     
    

async def load_eval(org: str, request: Request) -> RedirectResponse:
    from os.path import exists

    if org == 'air-turquoise':
        open_evals = await db.get_open_evaluations(org)
        for item in open_evals.itertuples(index=None):
            fname = get_filename(item.item_name)
            if exists(fname):
                print('extracting', item.item_name)
                evaluation = await airturquoise_loader.extract_pdf_data(item.item_name, fname)
                if evaluation is not None:
                    await db.save_evaluation(org, evaluation)
            else:
                print('skipping', item.item_name)

    return RedirectResponse(url=f"/{org}", status_code=303)         