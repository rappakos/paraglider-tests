# db.py
import aiosqlite
from sqlalchemy import create_engine,text
from pandas import DataFrame, read_sql_query

DB_NAME = './glider_tests.db'
INIT_SCRIPT = './glider_tests_app/init_db.sql'
START_DATE = '2020-01-01' # do not load earlier tests


async def setup_db(app):
    app['DB_NAME'] = DB_NAME
    async with aiosqlite.connect(DB_NAME) as db:
        # only test
        async with db.execute("SELECT 1") as cursor:
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
                            , count(distinct r.[item_name]) [item_count]
                            , max(r.[report_date]) [max_date]
                            , min(r.[report_date]) [min_date]
                            , count(distinct e.[item_name]) [eval_count]
                        FROM air_turquoise_reports r  
                        LEFT JOIN air_turquoise_evaluation e ON e.[item_name]=r.[item_name]
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
                            ,  count(e.test_value) [evaluation]
                        FROM air_turquoise_reports r  
                        LEFT JOIN air_turquoise_evaluation e ON e.[item_name]=r.[item_name]
                        GROUP BY r.[report_date], r.[item_name], r.[report_link], r.[report_class], r.[download_link]
                        HAVING  r.[report_link] IS NULL OR r.[download_link] IS NULL OR count(e.test_value)=0
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
        if org != 'air-turquoise':
            return DataFrame()

        engine = create_engine(f'sqlite:///{DB_NAME}')
        with engine.connect() as db:
            param = {'item_name':item_name}
            df  = read_sql_query(text(f"""
                        SELECT e.[item_name], e.test_name [test], e.test_value [rating]
                        FROM air_turquoise_evaluation e 
                        WHERE e.[item_name] = :item_name
                    """), db, params=param)
        return df


async def get_evaluations(org:str):
        if org != 'air-turquoise':
            return DataFrame()

        engine = create_engine(f'sqlite:///{DB_NAME}')
        with engine.connect() as db:
            param = {}
            df  = read_sql_query(text(f"""
                        SELECT e.[item_name], e.test_name, e.test_value
                        FROM air_turquoise_evaluation e 
                    """), db, params=param)
        return df


async def save_evaluation(org:str, evaluation):
    if org=='air-turquoise':
        async with aiosqlite.connect(DB_NAME) as db:
            for params in evaluation.itertuples(index=False):
                #print(params)
                res = await db.execute_insert("""
                                INSERT OR IGNORE INTO air_turquoise_evaluation ([item_name], [test_name], [test_value])
                                SELECT :item_name, :test, :rating
                            """, params)
                #print(res)
            await db.commit()        
    else:
        print("not implemented yet")     


async def get_open_evaluations(org:str):
    if org != 'air-turquoise':
        return DataFrame()

    engine = create_engine(f'sqlite:///{DB_NAME}')
    with engine.connect() as db:
        param = {}
        df  = read_sql_query(text(f"""
                        SELECT r.[item_name]
                        FROM air_turquoise_reports r 
                        WHERE NOT EXISTS (select 1 from air_turquoise_evaluation e 
                                where e.[item_name]=r.[item_name])
                        ORDER BY r.[report_date] DESC,  r.[item_name] ASC
                        LIMIT 100 -- test
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
                        LIMIT 200 -- test
                    """), db, params=param)
        return df      

async def save_download_link(report_link, download_link):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""UPDATE air_turquoise_reports
                                SET download_link = ?
                                WHERE download_link IS NULL AND report_link = ?
                """, (download_link, report_link))             

        await db.commit()