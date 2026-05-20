from sqlalchemy import select
from app.models.user import User, UserRole
from app.repositories.base import BaseRepository


class UserRepository(BaseRepository):
    def __init__(self, session):
        self.session = session

    async def get_by_email(self, email: str) -> User | None:
        query = select(User).where(User.email == email)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()

    async def create(self, user: User) -> User:
        self.session.add(user)
        await self.session.commit()
        await self.session.refresh(user)
        return user

    async def get_courier_by_id(self, courier_id: int) -> User | None:
        query = select(User).where(User.id == courier_id, User.role == UserRole.COURIER)
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
