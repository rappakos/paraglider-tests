

DHV_TEST_PAGE_SIZE = 100
DHV_TEST_URL = f'https://www.dhv.de/db3/muster/liste?fmuster=&fhersteller=&fgeraeteart=2&fpruefstelle=0&s=1&count={DHV_TEST_PAGE_SIZE}&start={1+DHV_TEST_PAGE_SIZE*page_number}'
DHV_REPORT_URL = f'https://www.dhv.de/db1/technictestreport2.php?item=-{item_id}&lang=en'