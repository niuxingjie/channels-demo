import urllib

from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken, TokenError
from rest_framework_simplejwt.settings import api_settings

from channels.auth import AuthMiddleware, UserLazyObject
from channels.db import database_sync_to_async

User = get_user_model()


class CustomAuthMiddleware(AuthMiddleware):

    def populate_scope(self, scope):
        # Add it to the scope if it's not there already
        if "user" not in scope:
            scope["user"] = UserLazyObject()

    async def resolve_scope(self, scope):
        raw_token = self.get_raw_token(scope)
        validated_token = self.get_validated_token(raw_token)
        scope["user"]._wrapped = await self.get_user(validated_token)

    async def __call__(self, scope, receive, send):
        scope = dict(scope)
        # Scope injection/mutation per this middleware's needs.
        self.populate_scope(scope)
        # Grab the finalized/resolved scope
        await self.resolve_scope(scope)

        return await super().__call__(scope, receive, send)

    def get_raw_token(self, scope):
        """
        websocket的url：/ws/chat//?access_token=Bearer token...
        access_token格式: 'Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJ'
        """
        token = str(scope['query_string'].decode('utf-8'))
        token = urllib.parse.unquote(token)
        token = token.split(" ")[1].encode('utf-8')
        return token

    def get_validated_token(self, raw_token):
        """
        Validates an encoded JSON web token and returns a validated token
        wrapper object.
        """
        messages = []
        for AuthToken in api_settings.AUTH_TOKEN_CLASSES:
            try:
                return AuthToken(raw_token)
            except TokenError as e:
                messages.append(
                    {
                        "token_class": AuthToken.__name__,
                        "token_type": AuthToken.token_type,
                        "message": e.args[0],
                    }
                )

        raise InvalidToken(
            {
                "detail": _("Given token not valid for any token type"),
                "messages": messages,
            }
        )
    
    @database_sync_to_async
    def get_user(self, validated_token):
        """
        Attempts to find and return a user using the given validated token.
        """
        try:
            user_id = validated_token[api_settings.USER_ID_CLAIM]
        except KeyError:
            raise InvalidToken(_("Token contained no recognizable user identification"))

        try:
            user = User.objects.get(**{api_settings.USER_ID_FIELD: user_id})
        except User.DoesNotExist:
            raise AuthenticationFailed(_("User not found"), code="user_not_found")

        if not user.is_active:
            raise AuthenticationFailed(_("User is inactive"), code="user_inactive")

        return user