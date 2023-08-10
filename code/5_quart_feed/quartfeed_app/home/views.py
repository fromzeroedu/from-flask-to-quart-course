from quart import Blueprint

from typing import Union, TYPE_CHECKING

if TYPE_CHECKING:
    from werkzeug.wrappers.response import Response

home_app = Blueprint("home_app", __name__)


@home_app.route("/", methods=["GET"])
async def home() -> Union[str, "Response"]:
    return "<h1>Welcome to Quartfeed</h1>"
