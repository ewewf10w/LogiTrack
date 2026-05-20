from fastapi_users import schemas

from app.models.user import UserRole


class UserRead(schemas.BaseUser[int]):
    first_name: str
    last_name: str
    role: UserRole


class UserCreate(schemas.BaseUserCreate):
    first_name: str
    last_name: str


class EmployeeCreate(schemas.BaseUserCreate):
    first_name: str
    last_name: str
    role: UserRole


class UserUpdate(schemas.BaseUserUpdate):
    first_name: str | None = None
    last_name: str | None = None
