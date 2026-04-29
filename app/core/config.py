from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/logitrack"
    MAIL_SERVER: str = "localhost"
    MAIL_PORT: int = 1025

    class Config:
        env_file = ".env"


settings = Settings()
