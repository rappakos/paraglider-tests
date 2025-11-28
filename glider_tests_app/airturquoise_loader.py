# airturquoise_loader.py
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
from pypdf import PdfReader



AIR_TURQUOISE_PAGE_SIZE=25
AIR_TURQUISE_BASE_URL = 'https://para-test.com'
#AIR_TURQUISE_TEST_URL_OLD = 'https://para-test.com/component/jak2filter/?Itemid=114&issearch=1&isc=1&category_id=11&xf_3_txt={classification}&ordering=publishUp&orders[publishUp]=rpublishUp&orders[date]=date&start={index}'
AIR_TURQUISE_TEST_URL = 'https://para-test.com/reports?page=1&category=Glider_PG_&classification={classification}&page={index}#main-content'

TEST_PARAMS_TEMPLATE = [
    '(?:Test pilot)\s(?P<testpilots>\w+(\s+\w+)*)',
    '(?:Harness)\s(?P<harnesses>\w+(\s+[-\w]+)*)',
    '(?:Harness to risers distance \(cm\))\s(?P<depth_min>\d{2,3})\s(?P<depth_max>\d{2,3})',
    '(?:Distance between risers \(cm\))\s(?P<width_min>(\d{2,3}|0))\s(?P<width_max>\d{2,3})', 
    '(?:Total weight in flight \(kg\))\s(?P<weight_min>(\d{2,3}|0))\s(?P<weight_max>\d{2,3})'
]

TEST_PARAMS_OCR_TEMPLATE = [
    '(?:Test pilot)\s(?P<testpilots>\w+(\s+\w+)*)',
    '(?:Harness)\s(?P<harnesses>\w+(\s+[-\w]+)*)',
    '(?:Harness to risers distance(?: (\(cm\)|\[cm\]))?)\s(?P<depth_min>(\d{2,3}|n/a))\s(?P<depth_max>\d{2,3})', 
    '(?:(?:\(cm\) )?Distance between risers(?: (\(cm\)|\[cm\]))?)\s(?P<width_min>\d{2,3})\s(?P<width_max>\d{2,3})', # \(cm\) may be  somewere?
    '(?:(?:\(cm\) )?Total weight in flight(?: (\(kg\)|\[kg\]))?)\s(?P<weight_min>\d{2,3})\s(?P<weight_max>\d{2,3})'
]


TEXT_DATA_TEMPLATE = [
 'Test Report generated automatically(.+)(?P<test>1. Inflation/Take-off) (?P<rating>[A-D])',
 '(?P<test>2. Landing) (?P<rating>[A-D])',
 '(?P<test>3. Speed in straight flight) (?P<rating>[A-D])',
 '(?P<test>4. Control movement) (?P<rating>[A-D])',
 '(?P<test>5. Pitch stability exiting accelerated flight) (?P<rating>[0A-D])',
 '(?P<test>6. Pitch stability operating controls during accelerated\nflight)(?P<rating>[0A-D])', #  multiline!
 '(?P<test>7. Roll stability and damping) (?P<rating>[A-D])',
 '(?P<test>8. Stability in gentle spirals) (?P<rating>[A-D])',
 '(?P<test>9. Behaviour exiting a fully developed spiral dive) (?P<rating>[A-D])',
 '(?P<test>10. Symmetric front collapse) (?P<rating>[A-D])',
 '(?P<test>11. Exiting deep stall \(parachutal stall\)) (?P<rating>[0A-D])', # 0: not available?
 '(?P<test>12. High angle of attack recovery) (?P<rating>[A-D])',
 '(?P<test>13. Recovery from a developed full stall) (?P<rating>[A-D])',
 '(?P<test>14. Asymmetric collapse) (?P<rating>[A-D])',
 '(?P<test>15. Directional control with a maintained asymmetric\ncollapse)(?P<rating>[A-D])', # multiline!
 '(?P<test>16. Trim speed spin tendency) (?P<rating>[A-D])',
 '(?P<test>17. Low speed spin tendency) (?P<rating>[A-D])',
 '(?P<test>18. Recovery from a developed spin) (?P<rating>[A-D])',
 '(?P<test>19. B-line stall) (?P<rating>[0A-D])', # 0: not available
 '(?P<test>20. Big ears) (?P<rating>[A-D])',
 '(?P<test>21. Big ears in accelerated flight) (?P<rating>[0A-D])',
 '(?P<test>22. Alternative means of directional control) (?P<rating>[A-D])',
]

TEXT_DATA_OCR_TEMPLATE = [
 '(?P<test>1. Inflation/Take-off) (?P<rating>[a-dA-D])',
 '(?P<test>2. Landing) (?P<rating>[a-dA-D])',
 '(?P<test>3. Speed in straight flight) (?P<rating>[a-dA-D])',
 '(?P<test>4. Control movement) (?P<rating>[a-dA-D])',
 '(?P<test>5. Pitch stability exiting accelerated flight) (?P<rating>[0a-dA-D])',
 '(?P<test>6. Pitch stability operating controls during(?: accelerated)?) (?P<rating>[0a-dA-D])', #  multiline!
 '(?P<test>7. Roll stability and damping) (?P<rating>[a-dA-D])',
 '(?P<test>8. Stability in gentle spirals) (?P<rating>[a-dA-D])',
 '(?P<test>9. Behaviour exiting a fully developed spiral dive) (?P<rating>[a-dA-D])',
 '(?P<test>10. Symmetric front collapse) (?P<rating>[a-dA-D])',
 '(?P<test>11. Exiting deep stall \(parachutal stall\)) (?P<rating>[a-dA-D])',
 '(?P<test>12. High angle of attack recovery) (?P<rating>[a-dA-D])',
 '(?P<test>13. Recovery from a developed full stall) (?P<rating>[a-dA-D])',
 '(?P<test>14. Asymmetric collapse) (?P<rating>[a-dA-D])',
 '(?P<test>15. Directional control with a maintained(?: asymmetric)?) (?P<rating>[a-dA-D])', # multiline!
 '(?P<test>16. Trim speed spin tendency) (?P<rating>[a-dA-D])',
 '(?P<test>17. Low speed spin tendency) (?P<rating>[a-dA-D])',
 '(?P<test>18. Recovery from a developed spin) (?P<rating>[a-dA-D])',
 '(?P<test>19. B-line stall) (?P<rating>[0a-dA-D])', # 0: not available
 '(?P<test>20. Big ears) (?P<rating>[a-dA-D])',
 '(?P<test>21. Big ears in accelerated flight) (?P<rating>[0a-dA-D])',
 '(?P<test>22. Alternative means of directional control) (?P<rating>[a-dA-D])',
]


async def get_reports(classification:str, start_day:str):
    page,current_day = 0, datetime.now().isoformat()[:10] # going backwards
    pages = []
    while current_day > start_day:
        print(classification, page,current_day,start_day)
        index = page * AIR_TURQUOISE_PAGE_SIZE

        table_data = await get_table_data(classification, index)
        #print(classification, page, table_data.empty)
        new_data = table_data[table_data['report_date'] > start_day ]
        if not new_data.empty:
            pages.append(new_data)
        #print(table_data.to_markdown())
        # step forward
        if table_data.empty:
            current_day = min(table_data['report_date'])
            page = page + 1
        else:
            current_day = start_day # ???
    
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
        table_div = soup.find('div',{"id":"reportlist-ReportsList"})
        tbl = table_div.find('table')
        #assert(len(tbl.findAll('tr'))-1,AIR_TURQUOISE_PAGE_SIZE)
        for tr in tbl.findAll('tr')[1:]:
            #print(tr.prettify())
            td_list=tr.findAll('td')
            report_date = datetime.strptime(td_list[0].text.strip(), '%d.%m.%Y').strftime('%Y-%m-%d')
            item_name = td_list[1].text.strip()
            report_link = td_list[0].find('a')['href']
            report_class = td_list[2].text.strip()
            #print((report_date, item_name, report_link))
            data.append((report_date, item_name, report_link, report_class))
    except requests.exceptions.HTTPError as err:
        print(err)

    return pd.DataFrame(data, columns=['report_date','item_name','report_link','report_class'])

async def get_download_link(link:str):
    url = f"{AIR_TURQUISE_BASE_URL}/reports{link}"
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        #print(soup.prettify)
        table = soup.find("table")
        a = None
        a_de = None
        for tr in table.find("tbody").findAll('tr'):
            #print(tr)
            td = tr.find('td') # first
            alink = td.find('a')
            #print( alink.text if alink else '-' )
            if alink and alink.text.strip()=='Flight report':
                a = alink
            if alink and alink.text.strip()=='Flight report trimmer closed':
                a = alink     
            if alink and alink.text.strip()=='Flugbericht':
                a_de = alink     
            if a:
                break

        # UTurn Emotion 4 SM: EN <> DE
        # windtech-paragliders-honey-3-xs: only FR
        # supair-birdy-s: EN <> FR

        if a:
            #print(a.prettify())
            download_link = a['href']
            return download_link
        #elif a_de:
        #   download_link = a_de['href']
        #   return download_link.replace('_de.pdf','_en.pdf')

    except requests.exceptions.HTTPError as err:
        print(err)
    
    return None

async def extract_pdf_data(item_name:str, filename:str):
    textrows = await extract_textrows(item_name, filename)

    return pd.DataFrame(filter_evaluations(item_name, textrows))

async def extract_param_data(item_name:str, filename:str):
    textrows = await extract_textrows(item_name, filename)

    return filter_parameters(item_name, textrows)

async def extract_ocr_data(item_name:str, filename:str):
    import os
    from PIL import Image
    from pdf2image import convert_from_bytes
    import pytesseract

    pytesseract.pytesseract.tesseract_cmd = os.getenv('tesseract_cmd')
    #print(pytesseract.pytesseract.tesseract_cmd)

    textrows, failed = [], False
    pdf_file = convert_from_bytes(open(filename, 'rb').read())
    for (i,page) in enumerate(pdf_file) :
        try:
            text = pytesseract.image_to_string(page,config='--psm 4')
            lines = text.split('\n')
            # hacks
            hack = '21. Big ears in accelerated flight E . -'
            if hack in lines:
                lines[lines.index(hack)] = '21. Big ears in accelerated flight B'
            hack = 'Harness to risers distance (cm) M1 43'
            if hack in lines:
                lines[lines.index(hack)] = 'Harness to risers distance (cm) 41 43'

            textrows.extend(lines)

        except Exception as x:
            print(f"page {i} failed {x}")
            failed = False
            continue

    print(textrows)
    if not failed:
        params = filter_parameters(item_name, textrows, from_ocr=True)
        print(params)
        evaluations = filter_evaluations(item_name, textrows, from_ocr=True)
        return params, pd.DataFrame(evaluations)
    else:
        return None,  pd.DataFrame()


async def extract_textrows(item_name:str, filename:str):
    textrows = []
    reader = PdfReader(filename)
    for page in reader.pages:
        lines = page.extract_text().split('\n')
        textrows.extend(lines)
    
    return textrows


def filter_parameters(item_name:str, textrows, from_ocr=False):
    import re

    results= {'item_name':item_name}
    templates = TEST_PARAMS_OCR_TEMPLATE if from_ocr else TEST_PARAMS_TEMPLATE
    for i,pattern in enumerate(templates):
        rowindex = 0
        for j,row in enumerate(textrows[rowindex:]):
            #print(pattern,row)
            m = re.match(pattern,row)
            if m:
                #print(m.groupdict())
                # results = results | m.groupdict() # PY >= 3.9
                results = {**results, **m.groupdict()}
                rowindex += j
                break
        #if i==1 and rowindex==0:
        #    print("there was no match for the first entry")
        #    break

    return results

def filter_evaluations(item_name:str, textrows, from_ocr=False):
    import re

    results= []
    templates= TEXT_DATA_OCR_TEMPLATE if from_ocr else TEXT_DATA_TEMPLATE
    for i,pattern in enumerate(templates):
        rowindex, success = 0, False
        for j,row in enumerate(textrows[rowindex:]):
            if "\n" in pattern:
                doublerow = f"{row}\n{textrows[rowindex+j+1]}"
                m = re.match(pattern,doublerow,re.MULTILINE)
            else:
                m = re.match(pattern,row)
            if m:
                test,rating = m.group('test'), m.group('rating')
                rowindex += j
                success = True
                results.append({'item_name':item_name, 'test':test, 'rating': rating})
                break
        if not success:
            print(f"!!! Test {i+1} - {pattern} failed")
            if from_ocr and i+1 in [11,13]:
                test_name = {
                                11:'11. Exiting deep stall (parachutal stall)',
                                13:'13. Recovery from a developed full stall'
                            }
                results.append({'item_name':item_name, 'test':test_name[i+1], 'rating': 0})
        if i==1 and rowindex==0:
            print("there was no match for the first entry")
            break
    #print(len(TEXT_DATA_TEMPLATE),len(results))
    #assert(len(results)==0 or len(results)==len(TEXT_DATA_TEMPLATE))
    #print(results)
    if len(results)==len(templates):
        return results 
    else: 
        return None