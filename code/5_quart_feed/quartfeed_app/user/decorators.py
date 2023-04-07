from functools import wraps
from typing import Any
from quart import session, request, redirect, url_for


def login_required(f:Any) -> Any:
    @wraps(f)
    async def decorated_function(*args: Any, **kwargs: Any) -> Any:
        if session.get("username") is None:
            return redirect(url_for("user_app.login", next=request.url))
        return await f(*args, **kwargs)
    
    return decorated_function