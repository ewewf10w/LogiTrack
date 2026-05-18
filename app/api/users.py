from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.user import UserCreate, UserRead
from app.services.user_service import UserService
from app.repositories.user_repo import UserRepository

router = APIRouter(prefix="/users", tags=["Users"])


def get_user_service(db: AsyncSession = Depends(get_db)):
    repo = UserRepository(db)
    return UserService(repo)


@router.post("/", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate, service: UserService = Depends(get_user_service)
):
    try:
        new_user = await service.register_user(user_data)
        return new_user
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/by-email", response_model=UserRead)
async def get_user_by_email(
    email: EmailStr = Query(..., description="Email пользователя"),
    service: UserService = Depends(get_user_service),
):
    user = await service.user_repo.get_by_email(email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Пользователь с почтой {email} не найден",
        )
    return user
