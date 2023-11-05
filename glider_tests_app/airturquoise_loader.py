# airturquoise_loader.py
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime




AIR_TURQUOISE_PAGE_SIZE=25
AIR_TURQUISE_BASE_URL = 'https://para-test.com'
AIR_TURQUISE_TEST_URL = 'https://para-test.com/component/jak2filter/?Itemid=114&issearch=1&isc=1&category_id=11&xf_3_txt={classification}&ordering=publishUp&orders[publishUp]=rpublishUp&orders[date]=date&start={index}'

async def get_tests(start_day:str):
    # TODO different classes?
    classification = 'B'
    page,current_day = 0, datetime.now().isoformat()[:10] # going backwards
    pages = []
    while current_day > start_day:
        print(page,current_day,start_day)
        index = page * AIR_TURQUOISE_PAGE_SIZE

        table_data = await get_table_data(classification, index)
        print(table_data.head())
        pages.append(table_data)

        # step forward
        current_day = min(table_data['report_date'])
        page = page + 1
    
    return pages

async def get_table_data(classification, index):
    classification, index = classification, index
    url = eval(f"f'{AIR_TURQUISE_TEST_URL}'") # auto
    data = []
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        #print(soup.prettify)        
        tbl = soup.find('table',{"class":"itemList"})
        #assert(len(tbl.findAll('tr'))-1,AIR_TURQUOISE_PAGE_SIZE)
        for tr in tbl.findAll('tr')[1:]:
            #print(tr.prettify())
            report_date = datetime.strptime(tr.find('td',{"class":"catItemDateCreated"}).text.strip(), '%d.%m.%Y').strftime('%Y-%m-%d')  # TODO dd.mm.yyyy to yyyy-mm-dd
            report_class = tr.find('td',{"class":"classification"}).text.strip()
            report_anchor = tr.find('a')
            report_link, item_name = report_anchor['href'], report_anchor.text.strip()
            #print((report_date, item_name, report_link))
            data.append((report_date, item_name, report_link, report_class))
    except requests.exceptions.HTTPError as err:
        print(err)

    return pd.DataFrame(data, columns=['report_date','item_name','report_link','report_class'])
