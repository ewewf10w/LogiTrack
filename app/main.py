from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import app.models

# ROUTERS
from app.api.orders import router as order_router
from app.api.items import router as item_router

app = FastAPI(title="LogiTrack Project")

app.include_router(order_router)
app.include_router(item_router)


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
