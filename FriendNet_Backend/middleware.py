import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from channels.db import database_sync_to_async
import logging

logger = logging.getLogger(__name__)


class TokenAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        token = scope["query_string"].decode("utf-8").split("token=")[1]

        try:
            logger.info("decoded token.......................")
            decoded_token = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
            user_id = decoded_token.get("user_id")
            user = await self.get_user(user_id)
            scope["user"] = user
        except jwt.exceptions.InvalidTokenError as e:
            logger.error(f"Invalid token error: {e}")
            return None

        return await self.inner(scope, receive, send)

    @database_sync_to_async
    def get_user(self, user_id):
        User = get_user_model()
        return User.objects.get(id=user_id)
