# airturquoise_loader.py
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from pypdf import PdfReader



AIR_TURQUOISE_PAGE_SIZE=25
AIR_TURQUISE_BASE_URL = 'https://para-test.com'
AIR_TURQUISE_TEST_URL = 'https://para-test.com/component/jak2filter/?Itemid=114&issearch=1&isc=1&category_id=11&xf_3_txt={classification}&ordering=publishUp&orders[publishUp]=rpublishUp&orders[date]=date&start={index}'

TEXT_DATA_TEMPLATE = [
 'Test Report generated automatically {*}1. Inflation/Take-off {rating}',
 '2. Landing {rating}',
 '3. Speed in straight flight {rating}',
 '4. Control movement {rating}',
 '5. Pitch stability exiting accelerated flight {rating}',
 '6. Pitch stability operating controls during accelerated\nflight{rating}',
 '7. Roll stability and damping {rating}',
 '8. Stability in gentle spirals {rating}',
 '9. Behaviour exiting a fully developed spiral dive {rating}',
 '10. Symmetric front collapse {rating}',
 '11. Exiting deep stall (parachutal stall) {rating}',
 '12. High angle of attack recovery {rating}',
 '13. Recovery from a developed full stall {rating}',
 '14. Asymmetric collapse {rating}',
 '15. Directional control with a maintained asymmetric\ncollapse{rating}',
 '16. Trim speed spin tendency {rating}',
 '17. Low speed spin tendency {rating}',
 '18. Recovery from a developed spin {rating}',
 '19. B-line stall {rating}',
 '20. Big ears {rating}',
 '21. Big ears in accelerated flight {rating}',
 '22. Alternative means of directional control {rating}',
]


async def get_reports(classification:str, start_day:str):
    page,current_day = 0, datetime.now().isoformat()[:10] # going backwards
    pages = []
    while current_day > start_day:
        print(classification, page,current_day,start_day)
        index = page * AIR_TURQUOISE_PAGE_SIZE

        table_data = await get_table_data(classification, index)
        new_data = table_data[table_data['report_date'] > start_day ]
        if not new_data.empty:
            pages.append(new_data)

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

async def get_download_link(link:str):
    url = f"{AIR_TURQUISE_BASE_URL}{link}"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        #print(soup.prettify)
        a = soup.find("a",{"title":"Flight report"})
        if not a:
            a = soup.find("a",{"title":" Flight report"})
        if not a:
            a = soup.find("a",{"title":"Flight report "})
        if not a:
            a = soup.find("a",{"title":"Flight Reports"})
        if not a:
            a = soup.find("a",{"title":"Flight report EN"})
        if not a:
            a = soup.find("a",{"title":"Flight report trimmer closed"}) # tandems?
        if not a:
            a = soup.find("a",{"title":"Flight report trimmer closed "}) # tandems?                        
        if not a:
            a = soup.find("a",{"title":" Flight report trimmer closed"}) # tandems?            

        if a:
            #print(a.prettify())
            download_link = a['href']
            return download_link

    except requests.exceptions.HTTPError as err:
        print(err)
    
    return None

async def extract_pdf_data(filename:str):
    textrows = []
    reader = PdfReader(filename)
    for page in reader.pages:
        #lines = [l for l in page.extract_text().split('\n') if l[0].isdigit()]
        lines = page.extract_text().split('\n')
        textrows.extend(lines)

    return textrows