from typing import Any
from quart import Quart

from db import db_connection


def create_app(**config_overrides: Any) -> Quart:
    app = Quart(__name__)

    # Load config
    app.config.from_pyfile("settings.py")

    # Apply overrides for tests
    app.config.update(config_overrides)

    # Import Blueprints
    from user.views import user_app
    from relationship.views import relationship_app

    # Register Blueprints
    app.register_blueprint(user_app)
    app.register_blueprint(relationship_app)

    @app.before_serving
    async def create_db_conn() -> None:
        database = await db_connection()
        await database.connect()
        app.dbc = database  # type: ignore

    @app.after_serving
    async def close_db_conn() -> None:
        await app.dbc.disconnect()  # type: ignore

    return app
