import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime


DHV_TEST_PAGE_SIZE = 50
DHV_TEST_URL = 'https://www.dhv.de/db3/muster/liste?fmuster=&fhersteller=&fgeraeteart=2&fpruefstelle=0&fklasse%5B%5D={classification}&s=1&count={DHV_TEST_PAGE_SIZE}&start={1+DHV_TEST_PAGE_SIZE*index}&lang=en'
DHV_REPORT_URL = 'https://www.dhv.de/db1/technictestreport2.php?item=-{item_id}&lang=en'




async def get_reports(classification:str, start_day:str):
    page,current_day = 0, datetime.now().isoformat()[:10] # going backwards
    pages = []
    while current_day > start_day:
        print(classification, page,current_day,start_day)

        table_data = await get_table_data(classification, page)
        if table_data.empty:
            break
        new_data = table_data[table_data['report_date'] > start_day ]
        if not new_data.empty:
            pages.append(new_data)
        else:
            break

        # step forward
        current_day = min(table_data['report_date'])
        page = page + 1

    return pages

async def get_table_data(classification:str, index:int):
    url = eval(f"f'{DHV_TEST_URL}'") # auto
    data = []
    try:
        resp = requests.get(url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, 'html.parser')
        #print(soup.prettify)        
        test_list = soup.find('div',{"class":"mu_list"})
        for item in test_list.findAll('div',{"class":"mu_listRow"}):
            item_desc = item.find('div',{"class":"mu_listDescription"})
            if item_desc:
                #if classification=='B':
                #    print(item_desc.prettify)        
                header, details= item_desc.find("h2"), item_desc.find("p")
                if header and header.find('a') and details:
                    report_link, item_name = header.find('a')['href'], header['title'].strip()[len('Paraglider '):]
                    for stro in  details.findAll('strong'):
                        stro.decompose() # labels are not necessary
                    #print([s.strip() for s in details.decode_contents().split('<br/>')])
                    [type_test,report_class,weight_range] = [s.strip() for s in details.decode_contents().split('<br/>')]
                    report_date_str = type_test[type_test.index('(')+1:type_test.index(')')]
                    report_date = datetime.strptime(report_date_str, '%d.%m.%Y').strftime('%Y-%m-%d')
                    if report_date > '2019-01-01':
                        #print(index,report_date, item_name, report_link,report_class)
                        data.append((report_date, item_name, report_link, report_class))
                    else:
                        print(index, report_date, item_name, report_link,report_class)
                        break # exit loop over test_list

    except requests.exceptions.HTTPError as err:
        print(err)

    return pd.DataFrame(data, columns=['report_date','item_name','report_link','report_class'])



async def extract_data(item_name:str, report_link:str):
    import pandas as pd
    print(item_name,report_link)

    params= {'item_name':item_name}
    evaluations = []
    # dummy
    evaluations.append({'item_name':item_name, 'test':'test', 'rating': 0})
    # TODO load

    return params, pd.DataFrame(evaluations)
