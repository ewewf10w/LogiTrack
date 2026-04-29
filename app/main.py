from fastapi import FastAPI

# ROUTERS
from app.api.orders import router as order_router

app = FastAPI(title="LogiTrack Project")

app.include_router(order_router)


@app.get("/")
async def root():
    return {"message": "Welcome to LogiTrack API"}


@app.get("/healthcheck")
async def healthcheck():
    return {"status": "ok"}
