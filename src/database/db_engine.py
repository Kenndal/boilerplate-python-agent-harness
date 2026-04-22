from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.config.config import config

async_engine = create_async_engine(
    config.DATABASE_URL,
    pool_pre_ping=True,
    connect_args={"connect_timeout": 10},
)

AsyncSessionMaker = async_sessionmaker(
    bind=async_engine,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
    class_=AsyncSession,
)
