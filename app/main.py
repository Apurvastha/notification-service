from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.config import settings
from app.database import engine
from app.routers import notifications, auth
from app.routers.websocket import router as websocket_router
from app.middleware import RequestLoggingMiddleware, AuditMiddleware
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(name)s %(message)s',
)


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


# middleware runs in reverse order — CORSMiddleware wraps everything
app.add_middleware(AuditMiddleware)
app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_methods=['*'],
    allow_headers=['*'],
)


app.include_router(auth.router)
app.include_router(notifications.router)
app.include_router(websocket_router)


@app.get('/health')
async def health():
    return {'status': 'ok', 'service': settings.APP_NAME}


@app.get('/ws/stats')
async def websocket_stats():
    """Shows how many users are connected via websocket"""
    from app.websocket_manager import manager
    return {
        'connected_user:': manager.connected_user_count,
        'total_connections': manager.total_connection_count
    }
