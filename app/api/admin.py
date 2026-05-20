from fastapi import APIRouter, Depends, HTTPException, status
from app.models.user import User, UserRole
from app.authentication.schemas.user import UserRead, EmployeeCreate

from app.authentication.fastapi_users import fastapi_users
from app.authentication.helper.user_manager import get_user_manager

router = APIRouter(prefix="/admin", tags=["Admin (Управление персоналом)"])


# Зависимость для проверки прав администратора
async def check_admin_role(
    user: User = Depends(fastapi_users.current_user(active=True)),
):
    if user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Доступ разрешен только для Администраторов системы",
        )
    return user


@router.post(
    "/create-employee", response_model=UserRead, status_code=status.HTTP_201_CREATED
)
async def create_employee(
    employee_data: EmployeeCreate,
    admin: User = Depends(check_admin_role),
    user_manager=Depends(get_user_manager),
):
    if employee_data.role == UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Нельзя создать еще одного администратора через этот эндпоинт",
        )

    # Здесь мы вызываем чистый метод, который теперь просто прокидывает данные в super().create()
    return await user_manager.create(employee_data, safe=False)
