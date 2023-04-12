from databases import Database
import databases
from quart import current_app
import sqlalchemy

metadata = sqlalchemy.MetaData()


async def db_connection() -> Database:
    database_url = f"postgresql+asyncpg://{current_app.config['DB_USERNAME']}:"
    database_url += f"{current_app.config['DB_PASSWORD']}@"
    database_url += f"{current_app.config['DB_HOST']}:5432/"
    database_url += f"{current_app.config['DATABASE_NAME']}"
    database = Database(database_url, min_size=5, max_size=20)

    return database