from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from urllib.parse import parse_qs


@database_sync_to_async
def get_user(token_key):
    """
    Validate a JWT token and return the corresponding user.

    AccessToken is imported inside the function so it doesn't load
    during app startup, which prevents unnecessary initialization.
    """
    from django.contrib.auth.models import AnonymousUser
    from api.models import User
    from rest_framework_simplejwt.tokens import AccessToken

    try:
        token = AccessToken(token_key)
        user_id = token.get("user_id")
        return User.objects.get(id=user_id)
    except Exception:
        # Any failure (invalid token, expired token, user missing) returns an anonymous user
        return AnonymousUser()


class JwtAuthMiddleware(BaseMiddleware):
    """
    Custom ASGI middleware that authenticates WebSocket connections using a JWT
    provided in the query string.


    If a valid token is provided, scope["user"] is set accordingly.
    Otherwise, the connection continues as an anonymous user.
    """

    async def __call__(self, scope, receive, send):
        from django.contrib.auth.models import AnonymousUser

        try:
            # Extract token from query string, if present
            query_string = scope.get("query_string", b"").decode("utf-8")
            params = parse_qs(query_string)
            token = params.get("token", [None])[0]

            if token:
                scope["user"] = await get_user(token)
            else:
                scope["user"] = AnonymousUser()
        except Exception:
            # Always ensure scope has a valid user object,
            # even if something goes wrong parsing the query.
            scope["user"] = AnonymousUser()

        return await super().__call__(scope, receive, send)
