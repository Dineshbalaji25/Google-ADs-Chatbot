# database/connection.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import declarative_base
from config.config import settings

db_url = settings.database_url or "sqlite+aiosqlite:///./chatbot.db"

# sqlite requires check_same_thread=False for async/multithreaded access
connect_args = {"check_same_thread": False} if db_url.startswith("sqlite") else {}

engine = create_async_engine(db_url, echo=False, connect_args=connect_args)
AsyncSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
Base = declarative_base()

async def get_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
