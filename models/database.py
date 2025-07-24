from decouple import config
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = config(
    "DATABASE_URL", default="postgresql+asyncpg://postgres:password@db:5432/mydatabase"
)
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
)
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)
Base = declarative_base()
