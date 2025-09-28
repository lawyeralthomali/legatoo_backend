"""
Password Reset Migration Script

This script adds password reset fields to the users table.
"""

import asyncio
import os
from datetime import datetime
from dotenv import load_dotenv
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.exc import OperationalError

# Load environment variables
load_dotenv("supabase.env")

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite+aiosqlite:///./app.db"
)

engine = create_async_engine(DATABASE_URL, echo=True)

async def run_password_reset_migration():
    """Add password reset fields to users table."""
    print("Starting password reset migration...")
    async with engine.begin() as conn:
        try:
            # Check if columns already exist to prevent errors on re-run
            result = await conn.execute(text("PRAGMA table_info(users);"))
            columns = [row[1] for row in result.fetchall()]

            if "password_reset_token" not in columns:
                print("Adding 'password_reset_token' column to 'users' table...")
                await conn.execute(text("ALTER TABLE users ADD COLUMN password_reset_token VARCHAR(255);"))
                print("✅ 'password_reset_token' column added.")
                
                # Create index for uniqueness (SQLite doesn't support UNIQUE in ALTER TABLE)
                print("Creating unique index for password_reset_token...")
                await conn.execute(text("CREATE UNIQUE INDEX IF NOT EXISTS ix_users_password_reset_token ON users(password_reset_token);"))
                print("✅ Unique index created.")
            else:
                print("'password_reset_token' column already exists. Skipping.")

            if "password_reset_token_expires" not in columns:
                print("Adding 'password_reset_token_expires' column to 'users' table...")
                await conn.execute(text("ALTER TABLE users ADD COLUMN password_reset_token_expires DATETIME;"))
                print("✅ 'password_reset_token_expires' column added.")
            else:
                print("'password_reset_token_expires' column already exists. Skipping.")

            print("✅ Password reset migration completed successfully!")

        except OperationalError as e:
            print(f"Database Operational Error during migration: {e}")
            print("This might happen if the 'users' table does not exist yet. Ensure base tables are created first.")
        except Exception as e:
            print(f"An unexpected error occurred during migration: {e}")

if __name__ == "__main__":
    asyncio.run(run_password_reset_migration())
