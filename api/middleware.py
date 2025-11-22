from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from rest_framework_simplejwt.tokens import AccessToken
from urllib.parse import parse_qs

# Move these imports inside functions to avoid AppRegistryNotReady
# from django.contrib.auth.models import AnonymousUser 
# from api.models import User

@database_sync_to_async
def get_user(token_key):
    from django.contrib.auth.models import AnonymousUser
    from api.models import User
    try:
        token = AccessToken(token_key)
        user_id = token['user_id']
        return User.objects.get(id=user_id)
    except Exception as e:
        return AnonymousUser()

class JwtAuthMiddleware(BaseMiddleware):
    async def __call__(self, scope, receive, send):
        from django.contrib.auth.models import AnonymousUser
        
        try:
            # Get the token from the query string
            query_string = scope.get("query_string", b"").decode("utf-8")
            params = parse_qs(query_string)
            token = params.get("token", [None])[0]
            
            if token:
                scope['user'] = await get_user(token)
            else:
                scope['user'] = AnonymousUser()
        except Exception as e:
             scope['user'] = AnonymousUser()
            
        return await super().__call__(scope, receive, send)