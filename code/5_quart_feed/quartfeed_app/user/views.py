from quart import Blueprint, current_app, render_template

from user.models import user_table

user_app = Blueprint("user_app", __name__)


@user_app.route("/register", methods=["GET", "POST"])
async def register() -> str:
    return await render_template("user/register.html")
