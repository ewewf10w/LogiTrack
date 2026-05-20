from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import app.models

# ROUTERS
from app.api.orders import router as order_router
from app.api.items import router as item_router
from app.api.admin import router as admin_router


from app.authentication.fastapi_users import fastapi_users
from app.authentication.backend import authentication_backend
from app.authentication.schemas.user import UserRead, UserCreate, UserUpdate

app = FastAPI(title="LogiTrack Project")

app.include_router(order_router)
app.include_router(item_router)
app.include_router(
    fastapi_users.get_auth_router(authentication_backend),
    prefix="/api/auth",
    tags=["Auth"],
)
app.include_router(
    fastapi_users.get_register_router(UserRead, UserCreate),
    prefix="/auth",
    tags=["Auth"],
)
app.include_router(
    fastapi_users.get_users_router(UserRead, UserUpdate),
    prefix="/api/users",
    tags=["Users"],
)
app.include_router(admin_router)


@app.exception_handler(ValueError)
async def value_error_exception_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


@app.get("/")
async def root():
    return {"message": "Welcome to LogiTrack API"}


@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}
