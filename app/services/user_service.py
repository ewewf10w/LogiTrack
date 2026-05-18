from app.repositories.user_repo import UserRepository
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import hash_password


class UserService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def register_user(self, schema: UserCreate) -> User:
        if await self.user_repo.get_by_email(schema.email):
            raise ValueError("Пользователь с таким email уже зарегистрирован")

        hashed_pw = hash_password(schema.password)

        new_user = User(
            email=schema.email,
            hashed_password=hashed_pw,
            first_name=schema.first_name,
            last_name=schema.last_name,
            role=schema.role,
        )
        return await self.user_repo.create(new_user)
