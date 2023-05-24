from sqlalchemy import Table, Column, Integer, String
from typing import Optional

from databases.core import Database
from databases.interfaces import Record

from db import metadata

user_table = Table(
    "user",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("username", String(15), index=True, unique=True),
    Column("password", String(128)),
)

async def get_user_by_username(conn: Database, username: str) -> Optional[Record]:
    """Get a user by username"""
    query = user_table.select().where(user_table.c.username == username)
    return await conn.fetch_one(query=query)
