from typing import Union, TYPE_CHECKING

from quart import (
    Blueprint,
    current_app,
    flash,
    redirect,
    request,
    session,
    abort,
)

from user.decorators import login_required
from user.models import get_user_by_username
from relationship.models import existing_relationship, relationship_table

if TYPE_CHECKING:
    from werkzeug.wrappers.response import Response

relationship_app = Blueprint("relationship_app", __name__)


@relationship_app.route("/add_friend/<username>", methods=["GET"])
@login_required
async def add_friend(username: str) -> Union[str, "Response"]:
    conn = current_app.dbc  # type: ignore
    referrer = request.referrer
    logged_user_id = session["user_id"]

    # check if the user exists
    to_user_row = await get_user_by_username(conn, username)
    if not to_user_row:
        abort(404)

    # check if the relationship already exists
    if not await existing_relationship(conn, logged_user_id, to_user_row["id"]):
        # add the relationship
        query = relationship_table.insert().values(
            fm_user_id=logged_user_id, to_user_id=to_user_row["id"]
        )
        await conn.execute(query=query)
        await flash(f"Followed {username}")

    # redirect back to the calling url
    return redirect(referrer)


@relationship_app.route("/remove_friend/<username>", methods=["GET"])
@login_required
async def remove_friend(username: str) -> Union[str, "Response"]:
    conn = current_app.dbc  # type: ignore
    referrer = request.referrer
    logged_user_id = session["user_id"]

    # check if the user exists
    to_user_row = await get_user_by_username(conn, username)
    if not to_user_row:
        abort(404)

    # check if the relationship already exists
    if await existing_relationship(conn, logged_user_id, to_user_row["id"]):
        # add the relationship
        query = relationship_table.delete().where(
            (relationship_table.c.fm_user_id == logged_user_id)
            & (relationship_table.c.to_user_id == to_user_row["id"])
        )
        await conn.execute(query=query)
        await flash(f"Unfollowed {username}")

    # redirect back to the calling url
    return redirect(referrer)
