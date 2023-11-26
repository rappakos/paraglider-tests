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
 'Test Report generated automatically(.+)(?P<test>1. Inflation/Take-off) (?P<rating>[A-D])',
 '(?P<test>2. Landing) (?P<rating>[A-D])',
 '(?P<test>3. Speed in straight flight) (?P<rating>[A-D])',
 '(?P<test>4. Control movement) (?P<rating>[A-D])',
 '(?P<test>5. Pitch stability exiting accelerated flight) (?P<rating>[A-D])',
 '(?P<test>6. Pitch stability operating controls during accelerated\nflight)(?P<rating>[A-D])', #  multiline!
 '(?P<test>7. Roll stability and damping) (?P<rating>[A-D])',
 '(?P<test>8. Stability in gentle spirals) (?P<rating>[A-D])',
 '(?P<test>9. Behaviour exiting a fully developed spiral dive) (?P<rating>[A-D])',
 '(?P<test>10. Symmetric front collapse) (?P<rating>[A-D])',
 '(?P<test>11. Exiting deep stall \(parachutal stall\)) (?P<rating>[A-D])',
 '(?P<test>12. High angle of attack recovery) (?P<rating>[A-D])',
 '(?P<test>13. Recovery from a developed full stall) (?P<rating>[A-D])',
 '(?P<test>14. Asymmetric collapse) (?P<rating>[A-D])',
 '(?P<test>15. Directional control with a maintained asymmetric\ncollapse)(?P<rating>[A-D])', # multiline!
 '(?P<test>16. Trim speed spin tendency) (?P<rating>[A-D])',
 '(?P<test>17. Low speed spin tendency) (?P<rating>[A-D])',
 '(?P<test>18. Recovery from a developed spin) (?P<rating>[A-D])',
 '(?P<test>19. B-line stall) (?P<rating>[0A-D])', # 0: not available
 '(?P<test>20. Big ears) (?P<rating>[A-D])',
 '(?P<test>21. Big ears in accelerated flight) (?P<rating>[A-D])',
 '(?P<test>22. Alternative means of directional control) (?P<rating>[A-D])',
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

async def extract_pdf_data(item_name:str, filename:str):
    textrows = []
    reader = PdfReader(filename)
    for page in reader.pages:
        lines = page.extract_text().split('\n')
        textrows.extend(lines)

    return pd.DataFrame(filtered(item_name, textrows))


def filtered(item_name:str, textrows):
    import re

    results= []
    for i,pattern in enumerate(TEXT_DATA_TEMPLATE):

        rowindex = 0
        for j,row in enumerate(textrows[rowindex:]):
            if "\n" in pattern:
                doublerow = f"{row}\n{textrows[rowindex+j+1]}"
                m = re.match(pattern,doublerow,re.MULTILINE)
            else:
                m = re.match(pattern,row)
            if m:
                test,rating = m.group('test'), m.group('rating')
                rowindex += j
                results.append({'item_name':item_name, 'test':test, 'rating': rating})
                break
        if i==1 and rowindex==0:
            print("there was no match for the first entry")
            break
    #print(len(TEXT_DATA_TEMPLATE),len(results))
    assert(len(results)==0 or len(results)==len(TEXT_DATA_TEMPLATE))

    return results 