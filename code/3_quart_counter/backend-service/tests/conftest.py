from typing import AsyncGenerator
import pytest
from dynaconf import settings
from my_app.application import create_app
from quart import Quart
from quart.typing import TestClientProtocol
from sqlalchemy import create_engine
from sqlalchemy_utils import create_database, database_exists, drop_database
from typing_extensions import Never


@pytest.fixture(scope="function")
async def create_dbi() -> AsyncGenerator[dict, Never]:
    # We only need to switch environment when running tests locally
    if settings.ENV_FOR_DYNACONF == "DEVELOPMENT":
        settings.configure(ENV_FOR_DYNACONF="TESTING")
    
    db_test_url = f"postgresql://{settings['DB_USERNAME']}:"
    db_test_url += f"{settings['DB_PASSWORD']}@"
    db_test_url += f"{settings['DB_HOST']}/"
    db_test_url += f"{settings['DATABASE_NAME']}"

    # drop the database if it exists
    if database_exists(db_test_url):
        drop_database(db_test_url)
    
    # create the testing database
    create_database(db_test_url)

    yield {
        "db_test_url": db_test_url,
    }

    # Drop database after test is complete
    drop_database(db_test_url)


@pytest.fixture(scope="function")
async def create_test_app(create_dbi: dict[str, str]) -> AsyncGenerator[Quart, None]:
    app = await create_app()

    # Create engine and create all tables
    engine = create_engine(create_dbi["db_test_url"])
    metadata.create_all(engine)

    # Start the database connection
    await app.startup()
    
    yield app
    
    # Stop the database connection
    await app.shutdown()
    
    # Clean up
    metadata.drop_all(engine)
