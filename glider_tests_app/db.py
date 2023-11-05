# db.py
import aiosqlite
from sqlalchemy import create_engine,text
from pandas import DataFrame

DB_NAME = './glider_tests.db'
INIT_SCRIPT = './glider_tests_app/init_db.sql'
START_DATE = '2020-01-01' # do not load earlier tests


async def setup_db(app):
    app['DB_NAME'] = DB_NAME
    async with aiosqlite.connect(DB_NAME) as db:
        # only test
        async with db.execute("SELECT 'db check'") as cursor:
            async for row in cursor:
                print(row[0])

        #
        with open(INIT_SCRIPT, 'r') as sql_file:
            sql_script = sql_file.read()
            await db.executescript(sql_script)
            await db.commit()

async def get_start_date(org:str, classification: str):
        import pandas as pd
        if org != 'air-turquoise':
            return START_DATE

        engine = create_engine(f'sqlite:///{DB_NAME}')
        with engine.connect() as db:
            param = {'classification':classification}
            #print(param)
            df  = pd.read_sql_query(text(f"""
                        SELECT  MAX([report_date]) [report_date]
                        FROM air_turquoise_reports r  
                        WHERE [report_class]= :classification
                    """), db, params=param)
        return max(df['report_date'])

async def get_stats():
    import pandas as pd
    
    engine = create_engine(f'sqlite:///{DB_NAME}')
    with engine.connect() as db:
        param = {}
        df  = pd.read_sql_query(text(f"""
                        SELECT 
                            'Air Turquoise' [org]
                            , r.[report_class]
                            , count(r.[item_name]) [item_count]
                            , max(r.[report_date]) [max_date]
                            , min(r.[report_date]) [min_date]
                        FROM air_turquoise_reports r  
                        GROUP BY [report_class]                        
                        ORDER BY [report_class]  
                    """), db, params=param)
        return df

async def get_reports(org:str):
        import pandas as pd
        if org != 'air-turquoise':
            return pd.DataFrame()

        engine = create_engine(f'sqlite:///{DB_NAME}')
        with engine.connect() as db:
            param = {}
            df  = pd.read_sql_query(text(f"""
                        SELECT [report_date], [item_name], [report_link], [report_class], [download_link]
                        FROM air_turquoise_reports r  
                        ORDER BY [report_date] DESC
                        LIMIT 25
                    """), db, params=param)
        return df


async def save_tests(org:str, page:DataFrame):
    if org=='air-turquoise':
        await _save_air_turquoise_tests(page)
    else:
        print("not implemented yet")

async def _save_air_turquoise_tests(page:DataFrame):
    async with aiosqlite.connect(DB_NAME) as db:
        for params in page.itertuples(index=False):
            await db.execute_insert("""
                            INSERT INTO air_turquoise_reports ([report_date], [item_name], [report_link], [report_class])
                            SELECT :report_date, :item_name, :report_link, :report_class
                        """, params)
        await db.commit()