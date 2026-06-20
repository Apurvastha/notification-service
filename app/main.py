from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.database import engine, Base
from app.routers import notifications


@asynccontextmanager
async def lifespan(app: FastAPI):
   
    # Alembic handles schema
    yield
    # shutdown - close connections
    await engine.dispose()


app = FastAPI(
    title=settings.APP_NAME,
    description='Real-time notification microservice',
    version='1.0.0',
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*']
)

app.include_router(notifications.router)

@app.get('/health')
async def health():
    return {'status': 'ok'}