import logging
from typing import Optional, TYPE_CHECKING

from fastapi_users import (
    BaseUserManager,
    IntegerIDMixin,
)

from app.core.config import settings
from app.models import User
from app.models.user import UserRole
from app.schemas.user import UserCreate

if TYPE_CHECKING:
    from fastapi import Request

log = logging.getLogger(__name__)


class UserManager(IntegerIDMixin, BaseUserManager[User, int]):
    reset_password_token_secret = settings.access_token.reset_password_token_secret
    verification_token_secret = settings.access_token.verification_token_secret

    async def create(
        self,
        user_create: UserCreate,
        safe: bool = False,
        request: Optional["Request"] = None,
    ) -> User:
        """
        Идеальное переопределение создания пользователя без костылей.
        """
        # Если это публичная регистрация (safe=True),
        # то какая бы роль ни пришла в схеме, мы жестко ставим CUSTOMER
        if safe:
            user_create.role = UserRole.CUSTOMER

        # Если регистрирует админ (safe=False), библиотека сама возьмет
        # роль (COURIER или MANAGER), которую мы передали в схеме EmployeeCreate.

        # Отдаем управление базовому методу FastAPI-Users.
        # Он сам всё провалидирует, захэширует пароль и сохранит в базу!
        return await super().create(user_create, safe=safe, request=request)

    async def on_after_register(
        self,
        user: User,
        request: Optional["Request"] = None,
    ):
        log.warning(
            "User %r has registered with role %r.",
            user.id,
            user.role,
        )

    async def on_after_request_verify(
        self,
        user: User,
        token: str,
        request: Optional["Request"] = None,
    ):
        log.warning(
            "Verification requested for user %r. Verification token: %r",
            user.id,
            token,
        )

    async def on_after_forgot_password(
        self,
        user: User,
        token: str,
        request: Optional["Request"] = None,
    ):
        log.warning(
            "User %r has forgot their password. Reset token: %r",
            user.id,
            token,
        )
