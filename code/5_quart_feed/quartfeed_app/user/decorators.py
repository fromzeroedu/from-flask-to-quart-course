from functools import wraps
from typing import Any
from quart import session, request, redirect, url_for


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("username") is None:
            return redirect(url_for("user_app.login", next=request.url))
        return f(*args, **kwargs)
    
    return decorated_function