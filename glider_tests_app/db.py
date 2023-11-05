# db.py
import aiosqlite
from sqlalchemy import create_engine,text

DB_NAME = './glider_tests.db'
INIT_SCRIPT = './glider_tests_app/init_db.sql'
START_DATE = '2023-06-01' # do not load earlier


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

async def get_start_date(org:str):
    return START_DATE