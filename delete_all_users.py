"""
Simple script to delete all users from the users table and related data.

This script will delete:
- Subscriptions (linked to profiles)
- Profiles (linked to users)
- RefreshTokens (linked to users)
- QueryLogs (linked to users)
- KnowledgeDocuments (linked to users via uploaded_by)
- Users

Usage:
    python delete_all_users.py
"""

import asyncio
from app.db.database import AsyncSessionLocal
from app.models.user import User
from app.models.profile import Profile
from app.models.refresh_token import RefreshToken
from app.models.subscription import Subscription
from app.models.query_log import QueryLog
from app.models.legal_knowledge import KnowledgeDocument
from sqlalchemy import delete, select


async def delete_all_users():
    """Delete all users and their related data."""
    
    print("🗑️  Starting deletion of all users...")
    
    async with AsyncSessionLocal() as db:
        try:
            # Count users before deletion
            result = await db.execute(select(User))
            user_count = len(result.scalars().all())
            print(f"📊 Found {user_count} users to delete")
            
            if user_count == 0:
                print("ℹ️  No users found. Nothing to delete.")
                return
            
            # Delete in order to respect foreign key constraints
            
            # 1. Delete Subscriptions (references profiles.id)
            subscriptions_result = await db.execute(delete(Subscription))
            subscription_count = subscriptions_result.rowcount
            print(f"   ✓ Deleted {subscription_count} subscriptions")
            
            # 2. Delete Profiles (references users.id)
            profiles_result = await db.execute(delete(Profile))
            profile_count = profiles_result.rowcount
            print(f"   ✓ Deleted {profile_count} profiles")
            
            # 3. Delete RefreshTokens (references users.id)
            refresh_tokens_result = await db.execute(delete(RefreshToken))
            refresh_token_count = refresh_tokens_result.rowcount
            print(f"   ✓ Deleted {refresh_token_count} refresh tokens")
            
            # 4. Delete QueryLogs (references users.id)
            query_logs_result = await db.execute(delete(QueryLog))
            query_log_count = query_logs_result.rowcount
            print(f"   ✓ Deleted {query_log_count} query logs")
            
            # 5. Delete KnowledgeDocuments (references users.id via uploaded_by)
            # Set uploaded_by to NULL first, or delete documents
            knowledge_docs_result = await db.execute(
                select(KnowledgeDocument).where(KnowledgeDocument.uploaded_by.isnot(None))
            )
            knowledge_docs = knowledge_docs_result.scalars().all()
            knowledge_doc_count = len(knowledge_docs)
            
            # Option 1: Delete documents (uncomment if you want to delete)
            # await db.execute(delete(KnowledgeDocument).where(KnowledgeDocument.uploaded_by.isnot(None)))
            # print(f"   ✓ Deleted {knowledge_doc_count} knowledge documents")
            
            # Option 2: Just set uploaded_by to NULL (safer - keeps documents)
            if knowledge_doc_count > 0:
                for doc in knowledge_docs:
                    doc.uploaded_by = None
                print(f"   ✓ Updated {knowledge_doc_count} knowledge documents (removed user reference)")
            
            # 6. Finally, delete Users
            users_result = await db.execute(delete(User))
            deleted_user_count = users_result.rowcount
            print(f"   ✓ Deleted {deleted_user_count} users")
            
            # Commit all changes
            await db.commit()
            
            print(f"\n✅ Successfully deleted {deleted_user_count} users and all related data!")
            
        except Exception as e:
            print(f"\n❌ Error deleting users: {str(e)}")
            await db.rollback()
            raise


if __name__ == "__main__":
    print("=" * 60)
    print("DELETE ALL USERS SCRIPT")
    print("=" * 60)
    print("⚠️  WARNING: This will delete ALL users from the database!")
    print("=" * 60)
    
    # Confirm deletion
    response = input("\nAre you sure you want to delete all users? (yes/no): ").strip().lower()
    
    if response == "yes":
        asyncio.run(delete_all_users())
    else:
        print("❌ Deletion cancelled.")

