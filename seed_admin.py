import asyncio
from pwdlib import PasswordHash

from app.models.db_helper import db_helper
from app.models.user import User, UserRole


async def create_super_admin():
    password_hash = PasswordHash.recommended()
    hashed_password = password_hash.hash("admin_super_password_2026")

    async for session in db_helper.session_getter():
        from sqlalchemy import select

        result = await session.execute(
            select(User).where(User.email == "admin@logitrack.ru")
        )
        if result.scalar_one_or_none():
            print("❌ Администратор уже существует в базе данных!")
            return

        admin = User(
            email="admin@logitrack.ru",
            hashed_password=hashed_password,
            first_name="Главный",
            last_name="Администратор",
            role=UserRole.ADMIN,
            is_active=True,
            is_verified=True,
            is_superuser=True,
        )

        session.add(admin)
        await session.commit()
        print("Супер-администратор успешно создан!")
        print("Email: admin@logitrack.ru")
        print("Пароль: admin_super_password_2026")


if __name__ == "__main__":
    asyncio.run(create_super_admin())
