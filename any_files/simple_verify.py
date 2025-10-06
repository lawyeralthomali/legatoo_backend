#!/usr/bin/env python3
"""
Simple Email Verification Script

Quick script to verify a user's email by updating the database.
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append('.')

from app.db.database import AsyncSessionLocal
from app.models.user import User
from app.models.profile import Profile
from sqlalchemy import select, update, delete


async def verify_email(email: str):
    """Verify user email by setting is_verified to True."""
    async with AsyncSessionLocal() as session:
        # Find user
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User '{email}' not found")
            return
        
        if user.is_verified:
            print(f"✅ User '{email}' already verified")
            return
        
        # Update verification status
        await session.execute(
            update(User).where(User.email == email).values(is_verified=True)
        )
        await session.commit()
        
        print(f"✅ Verified user '{email}'")


async def delete_profile(email: str):
    """Delete user profile by email."""
    async with AsyncSessionLocal() as session:
        # Find user
        result = await session.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User '{email}' not found")
            return
        
        # Find profile
        profile_result = await session.execute(
            select(Profile).where(Profile.user_id == user.id)
        )
        profile = profile_result.scalar_one_or_none()
        
        if not profile:
            print(f"⚠️ No profile found for user '{email}'")
            return
        
        # Delete profile
        await session.delete(profile)
        await session.commit()
        
        print(f"✅ Deleted profile for user '{email}'")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python simple_verify.py <email>")
        print("       python simple_verify.py --delete-profile <email>")
        sys.exit(1)
    
    if sys.argv[1] == "--delete-profile":
        if len(sys.argv) < 3:
            print("❌ Error: Email required for --delete-profile")
            sys.exit(1)
        email = sys.argv[2]
        asyncio.run(delete_profile(email))
    else:
        email = sys.argv[1]
        asyncio.run(verify_email(email))
