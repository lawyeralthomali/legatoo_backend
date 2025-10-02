#!/usr/bin/env python3
"""
Debug version of simple verification script
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append('.')

print("🔍 Starting debug script...")
print(f"🔍 Python path: {sys.path[:3]}...")

try:
    from app.db.database import AsyncSessionLocal
    print("✅ Database import successful")
except Exception as e:
    print(f"❌ Database import failed: {e}")
    sys.exit(1)

try:
    from app.models.user import User
    from app.models.profile import Profile
    print("✅ Model imports successful")
except Exception as e:
    print(f"❌ Model imports failed: {e}")
    sys.exit(1)

try:
    from sqlalchemy import select, update, delete
    print("✅ SQLAlchemy imports successful")
except Exception as e:
    print(f"❌ SQLAlchemy imports failed: {e}")
    sys.exit(1)


async def debug_delete_profile(email: str):
    """Debug version of profile deletion."""
    print(f"🔍 Attempting to delete profile for: {email}")
    
    try:
        async with AsyncSessionLocal() as session:
            print("✅ Database session created")
            
            # Find user
            print("🔍 Searching for user...")
            result = await session.execute(select(User).where(User.email == email))
            user = result.scalar_one_or_none()
            
            if not user:
                print(f"❌ User '{email}' not found")
                return
            
            print(f"✅ User found: ID={user.id}, Email={user.email}")
            
            # Find profile
            print("🔍 Searching for profile...")
            profile_result = await session.execute(
                select(Profile).where(Profile.user_id == user.id)
            )
            profile = profile_result.scalar_one_or_none()
            
            if not profile:
                print(f"⚠️ No profile found for user '{email}'")
                return
            
            print(f"✅ Profile found: ID={profile.id}, Name={profile.first_name} {profile.last_name}")
            
            # Delete profile
            print("🔍 Deleting profile...")
            await session.delete(profile)
            await session.commit()
            
            print(f"✅ Deleted profile for user '{email}'")
            
    except Exception as e:
        print(f"❌ Error in delete_profile: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🔍 Script started")
    print(f"🔍 Arguments: {sys.argv}")
    
    if len(sys.argv) < 2:
        print("❌ Error: No arguments provided")
        print("Usage: python debug_verify.py --delete-profile <email>")
        sys.exit(1)
    
    if sys.argv[1] == "--delete-profile":
        if len(sys.argv) < 3:
            print("❌ Error: Email required for --delete-profile")
            sys.exit(1)
        email = sys.argv[2]
        print(f"🔍 Running delete_profile for: {email}")
        asyncio.run(debug_delete_profile(email))
    else:
        print(f"❌ Unknown command: {sys.argv[1]}")
        sys.exit(1)
    
    print("🔍 Script completed")
