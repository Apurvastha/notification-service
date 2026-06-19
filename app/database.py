from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from app.config import settings


# async engine - non-blocking DB connections
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,  # logs sql when debug=true
    pool_size=10,
    max_overflow=20,
)

# session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


# base class for all models
class Base(DeclarativeBase):
    pass


# dependency - yields a DB session for each request
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise