from sqlalchemy import Column, Table, Integer, ForeignKey
from typing import Optional, TYPE_CHECKING

from db import metadata


if TYPE_CHECKING:
    from databases.core import Database
    from databases.interfaces import Record

relationship_table = Table(
    "relationship",
    metadata,
    Column("id", Integer, primary_key=True),
    Column("fm_user_id", Integer, ForeignKey("user.id")),
    Column("to_user_id", Integer, ForeignKey("user.id")),
)


async def existing_relationship(
    conn: "Database", fm_user_id: str, to_user_id: str
) -> Optional["Record"]:
    query = relationship_table.select().where(
        (relationship_table.c.fm_user_id == fm_user_id)
        & (relationship_table.c.to_user_id == to_user_id)
    )
    return await conn.fetch_one(query=query)
