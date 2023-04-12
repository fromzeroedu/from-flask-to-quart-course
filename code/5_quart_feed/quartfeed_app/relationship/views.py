from quart import Blueprint

relationship_app = Blueprint("relationship_app", __name__)


@relationship_app.route("/add_friend/<username>", methods=["GET"])
async def add_friend(username: str) -> str:
    return "added friend: " + username