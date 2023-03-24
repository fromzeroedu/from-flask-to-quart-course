from quart import Blueprint, current_app, redirect, render_template, request, session, redirect, url_for, flash, abort
from passlib.hash import pbkdf2_sha256
import uuid
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from werkzeug.wrappers.response import Response

from user.models import user_table
from relationship.models import relationship_table

user_app = Blueprint("user_app", __name__)


@user_app.route("/register", methods=["GET", "POST"])
async def register() -> Union[str, "Response"]:
    error: str = ""
    username: str = ""
    password: str = ""
    csrf_token: uuid.UUID = uuid.uuid4()

    if request.method == "GET":
        session["csrf_token"] = str(csrf_token)

    if request.method == "POST":
        form = await request.form
        username = form.get("username", "")
        password = form.get("password", "")

        # check empty values
        if not username or not password:
            error = "Please enter username and password"

        if session.get("csrf_token") != form.get("csrf_token") and not current_app.config.get("TESTING"):
            error = "Invalid POST contents"
        
        # check if the user exists
        conn = current_app.dbc  # type: ignore
        query = user_table.select().where(user_table.c.username == username)
        row = await conn.fetch_one(query=query)
        if row:
            error = "Username already exists"

        if not error:
            # register the user on the database
            if session.get("csrf_token"):
                del session["csrf_token"]

            hash: str = pbkdf2_sha256.hash(password)
            stmt = user_table.insert().values(username=username, password=hash)
            result = await conn.execute(stmt)
            await conn.execute("commit")
            await flash("You have been registered, please login")
            return redirect(url_for('.login'))
        else:
            session["csrf_token"] = str(csrf_token)

    return await render_template(
        "user/register.html", error=error, username=username, csrf_token=csrf_token
    )


@user_app.route("/login", methods=["GET", "POST"])
async def login() -> str:
    error: str = ""
    username: str = ""
    password: str = ""
    csrf_token: uuid.UUID = uuid.uuid4()

    if request.method == "GET":
        session["csrf_token"] = str(csrf_token)

    if request.method == "POST":
        form = await request.form
        username = form.get("username", "")
        password = form.get("password", "")

        # check empty values
        if not username or not password:
            error = "Please enter username and password"

        # check CSRF token
        elif session.get("csrf_token") != form.get("csrf_token"):
            error = "Invalid POST contents"

        # check if user exists
        else:
            conn = current_app.dbc  # type: ignore
            query = user_table.select().where(user_table.c.username == username)
            row = await conn.fetch_one(query=query)
            if not row:
                error = "User not found"
            else:
                # check the password
                if not pbkdf2_sha256.verify(password, row["password"]):
                    error = "User not found"

        if not error:
            # login the user
            del session["csrf_token"]
            session["user_id"] = row["id"]
            session["username"] = row["username"]
            return "User logged in"
        else:
            session["csrf_token"] = str(csrf_token)

    return await render_template(
        "user/login.html", error=error, username=username, csrf_token=csrf_token
    )


@user_app.route("/logout", methods=["GET",])
async def logout() -> "Response":
    del session["user_id"]
    del session["username"]
    return redirect(url_for(".login"))


@user_app.route("/user/<username>")
async def profile(username: str) -> Union[str, "Response"]:
    # fetch the user
    conn = current_app.dbc  # type: ignore
    query = user_table.select().where(user_table.c.username == username)
    profile_user = await conn.fetch_one(query=query)

    # user not found
    if not profile_user:
        abort(404)

    relationship: str = ""

    # see if we're looking at our own profile
    if profile_user.id == session.get("user_id"):
        relationship = "self"
    else:
        query = relationship_table.select().where(
            (relationship_table.c.fm_user_id == session.get("user_id"))
            & (relationship_table.c.to_user_id == profile_user.id)
        )
        relationship_record = await conn.fetch_one(query=query)
        if relationship_record:
            relationship = "following"
        else:
            relationship = "not_following"

    return await render_template(
        "user/profile.html", username=username, relationship=relationship
    )