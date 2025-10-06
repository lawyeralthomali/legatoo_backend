#!/usr/bin/env python3
"""
Email Verification Script

This script allows you to manually verify a user's email by updating their 
is_verified status in the database to True.

Usage:
    python verify_email_script.py <email>
    
Example:
    python verify_email_script.py user@example.com
"""

import asyncio
import sys
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

# Add the app directory to the Python path
sys.path.append('.')

from app.db.database import AsyncSessionLocal
from app.models.user import User
from app.models.profile import Profile


async def verify_user_email(email: str) -> bool:
    """
    Verify a user's email by setting is_verified to True.
    
    Args:
        email: The email address of the user to verify
        
    Returns:
        bool: True if verification was successful, False otherwise
    """
    try:
        async with AsyncSessionLocal() as session:
            # Find the user by email
            result = await session.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                print(f"❌ User with email '{email}' not found.")
                return False
            
            # Check if already verified
            if user.is_verified:
                print(f"✅ User '{email}' is already verified.")
                return True
            
            # Update the user's verification status
            await session.execute(
                update(User)
                .where(User.email == email)
                .values(is_verified=True)
            )
            
            await session.commit()
            
            print(f"✅ Successfully verified user '{email}'")
            return True
            
    except Exception as e:
        print(f"❌ Error verifying user '{email}': {str(e)}")
        return False


async def delete_user_profile(email: str) -> bool:
    """
    Delete a user's profile by email address.
    
    Args:
        email: The email address of the user whose profile to delete
        
    Returns:
        bool: True if deletion was successful, False otherwise
    """
    try:
        async with AsyncSessionLocal() as session:
            # Find the user by email
            result = await session.execute(
                select(User).where(User.email == email)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                print(f"❌ User with email '{email}' not found.")
                return False
            
            # Find the user's profile
            profile_result = await session.execute(
                select(Profile).where(Profile.user_id == user.id)
            )
            profile = profile_result.scalar_one_or_none()
            
            if not profile:
                print(f"⚠️ No profile found for user '{email}'.")
                return True  # Consider this successful since there's nothing to delete
            
            # Delete the profile
            await session.delete(profile)
            await session.commit()
            
            print(f"✅ Successfully deleted profile for user '{email}'")
            return True
            
    except Exception as e:
        print(f"❌ Error deleting profile for user '{email}': {str(e)}")
        return False


async def list_unverified_users():
    """List all unverified users in the database."""
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(User).where(User.is_verified == False)
            )
            users = result.scalars().all()
            
            if not users:
                print("✅ All users are verified!")
                return
            
            print(f"📋 Found {len(users)} unverified users:")
            for user in users:
                print(f"  - {user.email} (ID: {user.id})")
                
    except Exception as e:
        print(f"❌ Error listing users: {str(e)}")


async def list_users_with_profiles():
    """List all users and their profile status."""
    try:
        async with AsyncSessionLocal() as session:
            # Get all users with their profiles
            result = await session.execute(
                select(User, Profile).outerjoin(Profile, User.id == Profile.user_id)
            )
            user_profile_pairs = result.all()
            
            if not user_profile_pairs:
                print("📋 No users found in the database.")
                return
            
            print(f"📋 Found {len(user_profile_pairs)} users:")
            for user, profile in user_profile_pairs:
                profile_status = "✅ Has profile" if profile else "❌ No profile"
                verification_status = "✅ Verified" if user.is_verified else "❌ Unverified"
                print(f"  - {user.email} (ID: {user.id}) - {verification_status} - {profile_status}")
                
    except Exception as e:
        print(f"❌ Error listing users with profiles: {str(e)}")


async def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) < 2:
        print("Usage: python verify_email_script.py <email>")
        print("       python verify_email_script.py --list")
        print("       python verify_email_script.py --list-all")
        print("       python verify_email_script.py --delete-profile <email>")
        print("\nExamples:")
        print("  python verify_email_script.py user@example.com")
        print("  python verify_email_script.py --list")
        print("  python verify_email_script.py --list-all")
        print("  python verify_email_script.py --delete-profile user@example.com")
        sys.exit(1)
    
    command = sys.argv[1]
    
    if command == "--list":
        await list_unverified_users()
    elif command == "--list-all":
        await list_users_with_profiles()
    elif command == "--delete-profile":
        if len(sys.argv) < 3:
            print("❌ Error: Email required for --delete-profile")
            print("Usage: python verify_email_script.py --delete-profile <email>")
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
