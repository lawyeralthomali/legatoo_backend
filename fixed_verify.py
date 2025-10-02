#!/usr/bin/env python3
"""
Fixed Email Verification Script - Uses raw SQL to avoid relationship issues
"""

import asyncio
import sys
import os

# Add the app directory to the Python path
sys.path.append('.')

from app.db.database import AsyncSessionLocal
from sqlalchemy import text


async def verify_user_email(email: str) -> bool:
    """
    Verify a user's email by setting is_verified to True using raw SQL.
    
    Args:
        email: The email address of the user to verify
        
    Returns:
        bool: True if verification was successful, False otherwise
    """
    try:
        async with AsyncSessionLocal() as session:
            # Check if user exists
            result = await session.execute(
                text("SELECT id, is_verified FROM users WHERE email = :email"),
                {"email": email}
            )
            user = result.fetchone()
            
            if not user:
                print(f"❌ User with email '{email}' not found.")
                return False
            
            # Check if already verified
            if user.is_verified:
                print(f"✅ User '{email}' is already verified.")
                return True
            
            # Update the user's verification status
            await session.execute(
                text("UPDATE users SET is_verified = 1 WHERE email = :email"),
                {"email": email}
            )
            
            await session.commit()
            
            print(f"✅ Successfully verified user '{email}'")
            return True
            
    except Exception as e:
        print(f"❌ Error verifying user '{email}': {str(e)}")
        return False


async def delete_user_profile(email: str) -> bool:
    """
    Delete a user's profile by email address using raw SQL.
    
    Args:
        email: The email address of the user whose profile to delete
        
    Returns:
        bool: True if deletion was successful, False otherwise
    """
    try:
        async with AsyncSessionLocal() as session:
            # Find the user by email
            result = await session.execute(
                text("SELECT id FROM users WHERE email = :email"),
                {"email": email}
            )
            user = result.fetchone()
            
            if not user:
                print(f"❌ User with email '{email}' not found.")
                return False
            
            # Check if profile exists
            profile_result = await session.execute(
                text("SELECT id FROM profiles WHERE user_id = :user_id"),
                {"user_id": user.id}
            )
            profile = profile_result.fetchone()
            
            if not profile:
                print(f"⚠️ No profile found for user '{email}'.")
                return True  # Consider this successful since there's nothing to delete
            
            # Delete the profile
            await session.execute(
                text("DELETE FROM profiles WHERE user_id = :user_id"),
                {"user_id": user.id}
            )
            await session.commit()
            
            print(f"✅ Successfully deleted profile for user '{email}'")
            return True
            
    except Exception as e:
        print(f"❌ Error deleting profile for user '{email}': {str(e)}")
        return False


async def list_unverified_users():
    """List all unverified users in the database using raw SQL."""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("SELECT id, email FROM users WHERE is_verified = 0")
            )
            users = result.fetchall()
            
            if not users:
                print("✅ All users are verified!")
                return
            
            print(f"📋 Found {len(users)} unverified users:")
            for user in users:
                print(f"  - {user.email} (ID: {user.id})")
                
    except Exception as e:
        print(f"❌ Error listing users: {str(e)}")


async def list_users_with_profiles():
    """List all users and their profile status using raw SQL."""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("""
                SELECT u.id, u.email, u.is_verified, p.id as profile_id
                FROM users u
                LEFT JOIN profiles p ON u.id = p.user_id
                ORDER BY u.id
            """))
            users = result.fetchall()
            
            if not users:
                print("📋 No users found in the database.")
                return
            
            print(f"📋 Found {len(users)} users:")
            for user in users:
                profile_status = "✅ Has profile" if user.profile_id else "❌ No profile"
                verification_status = "✅ Verified" if user.is_verified else "❌ Unverified"
                print(f"  - {user.email} (ID: {user.id}) - {verification_status} - {profile_status}")
                
    except Exception as e:
        print(f"❌ Error listing users with profiles: {str(e)}")


async def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python fixed_verify.py <email>")
        print("       python fixed_verify.py --list")
        print("       python fixed_verify.py --list-all")
        print("       python fixed_verify.py --delete-profile <email>")
        print("\nExamples:")
        print("  python fixed_verify.py user@example.com")
        print("  python fixed_verify.py --list")
        print("  python fixed_verify.py --list-all")
        print("  python fixed_verify.py --delete-profile user@example.com")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "--list":
        await list_unverified_users()
    elif command == "--list-all":
        await list_users_with_profiles()
    elif command == "--delete-profile":
        if len(sys.argv) < 3:
            print("❌ Error: Email required for --delete-profile")
            print("Usage: python fixed_verify.py --delete-profile <email>")
            sys.exit(1)
        email = sys.argv[2]
        success = await delete_user_profile(email)
        sys.exit(0 if success else 1)
    else:
        # Default: verify email
        email = sys.argv[1]
        success = await verify_user_email(email)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    asyncio.run(main())
