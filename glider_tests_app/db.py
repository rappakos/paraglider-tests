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
        async with db.execute("SELECT count(*) FROM air_turquoise_tests") as cursor:
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
                        SELECT r.[report_date], r.[item_name], r.[report_link], r.[report_class], r.[download_link]
                            , case when count(e.test_id) > 0 then 1 else 0 end [evaluation]
                        FROM air_turquoise_reports r  
                        LEFT JOIN air_turquoise_evaluation e ON e.[item_name]=r.[item_name]
                        GROUP BY r.[report_date], r.[item_name], r.[report_link], r.[report_class], r.[download_link]
                        ORDER BY [report_date] DESC
                        LIMIT 500
                    """), db, params=param)
        return df

async def get_report_details(org:str, item_id:str):
        import pandas as pd
        if org != 'air-turquoise':
            return pd.DataFrame()

        engine = create_engine(f'sqlite:///{DB_NAME}')
        with engine.connect() as db:
            param = {}
            df  = pd.read_sql_query(text(f"""
                        SELECT [report_date], [item_name], [report_link], [report_class], [download_link]
                        FROM air_turquoise_reports r  
                        WHERE r.[report_link] = '/reports/item/{item_id}'
                    """), db, params=param)
        return df

async def get_evaluation(org:str, item_name:str):
        import pandas as pd
        if org != 'air-turquoise':
            return pd.DataFrame()

        engine = create_engine(f'sqlite:///{DB_NAME}')
        with engine.connect() as db:
            param = {}
            df  = pd.read_sql_query(text(f"""
                        SELECT r.[item_name], t.test_name [test], e.test_value [rating]
                        FROM air_turquoise_reports r  
                        INNER JOIN air_turquoise_evaluation e ON  r.[item_name]=e.[item_name]
                        INNER JOIN air_turquoise_tests t ON t.test_id = e.test_id
                        WHERE r.[item_name] = '{item_name}'
                    """), db, params=param)
        return df
async def save_evaluation(org:str, evaluation):
    if org=='air-turquoise':
        async with aiosqlite.connect(DB_NAME) as db:
            for params in evaluation.itertuples(index=False):
                #print(params)
                res = await db.execute_insert("""
                                INSERT OR IGNORE INTO air_turquoise_evaluation ([item_name], [test_id], [test_value])
                                SELECT :item_name, :test, :rating
                                FROM air_turquoise_tests t
                                WHERE t.[test_name]= :test
                            """, params)
                #print(res)
            await db.commit()        
    else:
        print("not implemented yet")     




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

async def get_open_reports(org:str):
        import pandas as pd
        if org != 'air-turquoise':
            return pd.DataFrame()

        engine = create_engine(f'sqlite:///{DB_NAME}')
        with engine.connect() as db:
            param = {}
            df  = pd.read_sql_query(text(f"""
                        SELECT [item_name], [report_link]
                        FROM air_turquoise_reports r 
                        WHERE [download_link] is null 
                        ORDER BY [report_date] DESC
                        LIMIT 20 -- test
                    """), db, params=param)
        return df 

async def get_download_links(org:str):
        import pandas as pd
        if org != 'air-turquoise':
            return pd.DataFrame()

        engine = create_engine(f'sqlite:///{DB_NAME}')
        with engine.connect() as db:
            param = {}
            df  = pd.read_sql_query(text(f"""
                        SELECT r.[item_name], r.[download_link]
                        FROM air_turquoise_reports r 
                        WHERE r.[download_link] is not null 
                        ORDER BY r.[report_date] DESC
                        LIMIT 150 -- test
                    """), db, params=param)
        return df      

async def save_download_link(report_link, download_link):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""UPDATE air_turquoise_reports
                                SET download_link = ?
                                WHERE download_link IS NULL AND report_link = ?
                """, (download_link, report_link))             

        await db.commit()