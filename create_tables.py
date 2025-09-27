#!/usr/bin/env python3
"""
Script to create SQLite database tables.
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv("supabase.env")

# Import after loading env vars
from app.db.database import engine, Base
from app.models import User, Profile, AccountType

async def create_all_tables():
    """Create all database tables."""
    print("Creating SQLite database tables...")
    
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
        print("✅ All tables created successfully!")
        
        # Print table info
        print("\nTables created:")
        print("- users")
        print("- profiles")
        print("- account_type (enum)")

if __name__ == "__main__":
    asyncio.run(create_all_tables())
