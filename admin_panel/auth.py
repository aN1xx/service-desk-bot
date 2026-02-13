"""
Admin panel authentication via signed cookies.
"""
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import RedirectResponse

from bot.config import settings

SESSION_COOKIE = "session_token"
SESSION_MAX_AGE = 86400  # 24 hours

_serializer = URLSafeTimedSerializer(settings.secret_key)


def create_session_token(username: str) -> str:
    return _serializer.dumps({"user": username})


def verify_session_token(token: str) -> str | None:
    """Returns username if valid, None otherwise."""
    try:
        data = _serializer.loads(token, max_age=SESSION_MAX_AGE)
        return data.get("user")
    except (BadSignature, SignatureExpired):
        return None


class AuthMiddleware(BaseHTTPMiddleware):
    """Redirects unauthenticated requests to /login."""

    OPEN_PATHS = ("/login", "/static")

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Allow open paths
        if any(path.startswith(p) for p in self.OPEN_PATHS):
            return await call_next(request)

        # Check session cookie
        token = request.cookies.get(SESSION_COOKIE)
        if not token or not verify_session_token(token):
            return RedirectResponse("/login", status_code=302)

        return await call_next(request)
