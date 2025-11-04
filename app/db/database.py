from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, relationship
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
    echo=False,  # Set to False to reduce noise
    future=True,
    pool_pre_ping=True,  # Verify connections before use
    pool_recycle=3600,   # Recycle connections every hour
    connect_args={
        "check_same_thread": False,  # SQLite specific
        "timeout": 30  # Connection timeout
    }
)

# Create async session factory - SQLAlchemy 1.4.23 compatible
from sqlalchemy.orm import sessionmaker
AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,  # Disable autoflush to prevent premature commits
    autocommit=False  # Explicit transaction control
)

# Base class for all models - SQLAlchemy 2.0 compatible
class Base(DeclarativeBase):
    pass

# Dependency to get database session
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        # Don't explicitly close - let the context manager handle it

# Function to create database tables and initialize super admin
async def create_tables():
    """Create all database tables and initialize super admin user."""
    # Import all models to ensure they are registered with SQLAlchemy
    from ..models import (
        User, Profile, RefreshToken,
        Subscription, Plan, Billing, UsageTracking, UserRole, Role,
        LawSource, LawArticle, LegalCase,
        CaseSection, LegalTerm, KnowledgeDocument, KnowledgeChunk,
        QueryLog,
        ContractTemplate, Contract,
        ContractLibrary, ContractTemplateLibrary, ContractRevision, ContractAIRequest,
        UserSession, LoginHistory, SystemLog,
    )
    
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    # Initialize super admin after tables are created
    await initialize_super_admin()

async def initialize_super_admin():
    """Initialize super admin user if it doesn't exist."""
    try:
        from ..services.user_management.super_admin_service import SuperAdminService
        
        async with AsyncSessionLocal() as db:
            super_admin_service = SuperAdminService()
            result = await super_admin_service.create_super_admin(db)
            
            if result.success:
                print("✅ Super admin initialized successfully")
            else:
                print(f"⚠️ Super admin initialization: {result.message}")
                
    except Exception as e:
        print(f"❌ Failed to initialize super admin: {str(e)}")
        # Don't raise the exception to avoid breaking database creation
