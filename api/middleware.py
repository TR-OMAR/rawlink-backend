from django.contrib.auth.models import AnonymousUser
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from rest_framework_simplejwt.tokens import AccessToken
# Removed top-level import of User to fix AppRegistryNotReady error
# from api.models import User 
from urllib.parse import parse_qs

@database_sync_to_async
def get_user(token_key):
    try:
        # Import User model here to avoid AppRegistryNotReady
        from api.models import User
        
        token = AccessToken(token_key)
        user_id = token['user_id']
        user = User.objects.get(id=user_id)
        print(f"✅ WS MIDDLEWARE: User found: {user.username} (ID: {user.id})")
        return user
    except Exception as e:
        print(f"❌ WS MIDDLEWARE: Token Error: {e}")
        return AnonymousUser()

class JwtAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        try:
            # Get the token from the query string
            query_string = scope.get("query_string", b"").decode("utf-8")
            params = parse_qs(query_string)
            token = params.get("token", [None])[0]
            
            if token:
                print(f"🔍 WS MIDDLEWARE: Token received: {token[:10]}...")
                scope['user'] = await get_user(token)
            else:
                print("⚠️ WS MIDDLEWARE: No token found in URL")
                scope['user'] = AnonymousUser()
        except Exception as e:
             print(f"❌ WS MIDDLEWARE: Critical Error: {e}")
             scope['user'] = AnonymousUser()
            
        return await super().__call__(scope, receive, send)