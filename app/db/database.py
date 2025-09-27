from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import String
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv("supabase.env")

# Database URL - Force SQLite (local file database)
DATABASE_URL = "sqlite+aiosqlite:///./app.db"

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Set to False in production
    future=True
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# Base class for all models
class Base(DeclarativeBase):
    pass

# Dependency to get database session
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

# Function to create database tables (only for our custom tables, not auth.users)
async def create_tables():
    async with engine.begin() as conn:
        # Only create our custom tables, not Supabase's auth.users
        await conn.run_sync(Base.metadata.create_all)
