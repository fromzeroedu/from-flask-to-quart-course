from quart import (
    Blueprint,
    current_app,
    redirect,
    render_template,
    request,
    session,
    redirect,
    url_for,
    flash,
    abort,
)
from passlib.hash import pbkdf2_sha256
import uuid
from typing import TYPE_CHECKING, Union

if TYPE_CHECKING:
    from werkzeug.wrappers.response import Response

from user.models import user_table, get_user_by_username
from relationship.models import relationship_table, existing_relationship
from user.decorators import login_required

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

        if session.get("csrf_token") != form.get(
            "csrf_token"
        ) and not current_app.config.get("TESTING"):
            error = "Invalid POST contents"

        # check if the user exists
        conn = current_app.dbc  # type: ignore
        user_row = await get_user_by_username(conn, username)
        if user_row:
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
            return redirect(url_for(".login"))
        else:
            session["csrf_token"] = str(csrf_token)

    return await render_template(
        "user/register.html",
        error=error,
        username=username,
        csrf_token=csrf_token,
    )


@user_app.route("/login", methods=["GET", "POST"])
async def login() -> Union[str, "Response"]:
    error: str = ""
    username: str = ""
    password: str = ""
    csrf_token: uuid.UUID = uuid.uuid4()

    if request.method == "GET":
        session["csrf_token"] = str(csrf_token)
        if request.args.get("next"):
            session["next"] = request.args.get("next")

    if request.method == "POST":
        form = await request.form
        username = form.get("username", "")
        password = form.get("password", "")

        # check empty values
        if not username or not password:
            error = "Please enter username and password"

        # check CSRF token
        elif (
            session.get("csrf_token") != form.get("csrf_token")
        ) and not current_app.testing:
            error = "Invalid POST contents"

        # check if user exists
        else:
            conn = current_app.dbc  # type: ignore
            user_row = await get_user_by_username(conn, username)
            if not user_row:
                error = "User not found"
            else:
                # check the password
                if not pbkdf2_sha256.verify(password, user_row["password"]):
                    error = "User not found"

        if user_row and not error:
            # login the user

            if not current_app.testing:
                del session["csrf_token"]

            session["user_id"] = user_row["id"]
            session["username"] = user_row["username"]

            if "next" in session:
                next = session["next"]
                session.pop("next")
                return redirect(next)
            else:
                return f"User @{session['username']} logged in"

        else:
            session["csrf_token"] = str(csrf_token)

    return await render_template(
        "user/login.html", error=error, username=username, csrf_token=csrf_token
    )


@user_app.route(
    "/logout",
    methods=[
        "GET",
    ],
)
async def logout() -> "Response":
    del session["user_id"]
    del session["username"]
    return redirect(url_for(".login"))


@user_app.route("/user/<username>")
@login_required
async def profile(username: str) -> Union[str, "Response"]:
    # fetch the user
    conn = current_app.dbc  # type: ignore
    profile_user = await get_user_by_username(conn, username)

    # user not found
    if not profile_user:
        abort(404)

    relationship: str = ""

    # see if we're looking at our own profile
    if profile_user.id == session.get("user_id"):  # type: ignore
        relationship = "self"
    else:
        if await existing_relationship(
            conn, session["user_id"], profile_user.id  # type: ignore
        ):
            relationship = "following"
        else:
            relationship = "not_following"

    return await render_template(
        "user/profile.html", username=username, relationship=relationship
    )
