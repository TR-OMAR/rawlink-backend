import logging
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from channels.exceptions import DenyConnection
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from api.models import User

# Configure logger
logger = logging.getLogger("ws_auth")

@database_sync_to_async
def get_user_from_token(token_key: str):
    """
    Fetch user from JWT token.
    Returns User object or raises exception.
    """
    try:
        token = AccessToken(token_key)
        user_id = token['user_id']
        user = User.objects.get(id=user_id)
        logger.info(f"✅ WS Auth Success: User {user.username} (ID: {user.id})")
        return user
    except Exception as e:
        logger.warning(f"❌ WS Auth Token Error: {e}")
        return AnonymousUser()


class JwtAuthMiddleware(BaseMiddleware):
    """
    Middleware for JWT authentication in Django Channels.
    Supports query string and Authorization header.
    """

    async def __call__(self, scope, receive, send):
        try:
            token = None

            # 1️⃣ Try query string first
            query_string = scope.get("query_string", b"").decode("utf-8")
            params = parse_qs(query_string)
            token = params.get("token", [None])[0]

            # 2️⃣ Fallback to Authorization header if not in query string
            if not token:
                headers = dict(scope.get("headers", []))
                auth_header = headers.get(b'authorization', b'').decode()
                if auth_header.startswith("Bearer "):
                    token = auth_header.split(" ")[1]

            # 3️⃣ Get user or deny connection
            if token:
                scope['user'] = await get_user_from_token(token)
                if scope['user'].is_anonymous:
                    logger.warning("⚠️ WS Auth: Invalid token, anonymous user assigned")
                    raise DenyConnection("Unauthorized")
            else:
                logger.warning("⚠️ WS Auth: No token provided")
                raise DenyConnection("Unauthorized")

        except DenyConnection as e:
            raise e
        except Exception as e:
            logger.error(f"❌ WS Middleware Error: {e}")
            raise DenyConnection("Unauthorized")

        return await super().__call__(scope, receive, send)
