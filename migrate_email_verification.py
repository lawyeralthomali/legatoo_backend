#!/usr/bin/env python3
"""
Database migration script to add email verification fields to users table.
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv("supabase.env")

# Import after loading env vars
from app.db.database import engine

async def migrate_users_table():
    """Add verification fields to users table."""
    print("Adding email verification fields to users table...")
    
    async with engine.begin() as conn:
        # Add verification_token column
        await conn.execute("""
            ALTER TABLE users 
            ADD COLUMN verification_token VARCHAR(255) NULL
        """)
        print("✅ Added verification_token column")
        
        # Add verification_token_expires column
        await conn.execute("""
            ALTER TABLE users 
            ADD COLUMN verification_token_expires DATETIME NULL
        """)
        print("✅ Added verification_token_expires column")
        
        # Create index on verification_token
        await conn.execute("""
            CREATE INDEX IF NOT EXISTS ix_users_verification_token 
            ON users(verification_token)
        """)
        print("✅ Created index on verification_token")
        
        print("\n🎉 Migration completed successfully!")

if __name__ == "__main__":
    asyncio.run(migrate_users_table())
