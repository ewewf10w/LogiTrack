from pydantic import BaseModel
from pydantic_settings import (
    BaseSettings,
    SettingsConfigDict,
)
from typing import Literal, Optional


class RunConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 8000
    reload: bool = True


class DatabaseConfig(BaseModel):
    url: str
    echo: bool = True
    echo_pool: bool = False
    pool_size: int = 50
    max_overflow: int = 10
    future: bool = True


class UrlPrefix(BaseModel):
    prefix: str = "/api"
    auth: str = "/auth"
    users: str = "/users"

    @property
    def bearer_token_url(self) -> str:
        parts = (self.prefix, self.auth, "/login")
        path = "".join(parts)
        return path.removeprefix("/")


class AuthConfig(BaseModel):
    cookie_max_age: int = 3600
    cookie_secure: bool = False
    cookie_samesite: Literal["lax", "strict", "none"] = "lax"


class AccessToken(BaseModel):
    secret: Optional[str] = None
    reset_password_token_secret: Optional[str] = None
    verification_token_secret: Optional[str] = None
    lifetime_seconds: int = 3600


class SmtpConfig(BaseModel):
    host: str = "127.0.0.1"
    port: int = 1025
    from_email: str = "no-reply@logitrack.com"
    user: Optional[str] = None
    password: Optional[str] = None


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(".env.template", ".env"),
        case_sensitive=False,
        env_nested_delimiter="__",
        env_prefix="APP_CONFIG__",
    )
    run: RunConfig = RunConfig()
    url: UrlPrefix = UrlPrefix()
    auth: AuthConfig = AuthConfig()
    db: DatabaseConfig = DatabaseConfig(
        url="postgresql+asyncpg://user:pass@localhost/dbname"
    )
    access_token: AccessToken
    smtp: SmtpConfig


settings = Settings()
