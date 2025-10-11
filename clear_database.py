"""
Clear Database Script

This script clears the database to allow re-upload with improved chunk format.
"""

import os
from pathlib import Path

def clear_database():
    """Delete the database file."""
    db_path = Path("app.db")
    
    print("=" * 80)
    print("DATABASE CLEANUP")
    print("=" * 80)
    
    if db_path.exists():
        print(f"\n📁 Found database: {db_path}")
        print(f"   Size: {db_path.stat().st_size / 1024 / 1024:.2f} MB")
        
        # Create backup
        backup_path = Path(f"app.db.backup_{int(__import__('time').time())}")
        print(f"\n📦 Creating backup: {backup_path}")
        import shutil
        shutil.copy(db_path, backup_path)
        print(f"✅ Backup created")
        
        # Delete database
        print(f"\n🗑️  Deleting database...")
        db_path.unlink()
        print(f"✅ Database deleted")
        
        print(f"\n✅ Database cleared successfully!")
        print(f"\nNext steps:")
        print(f"1. Start server: py start_server.py")
        print(f"2. Re-upload data: cd data_set && py batch_upload_json.py")
        print(f"3. Test accuracy: py test_retrieval_accuracy.py")
        
    else:
        print(f"\n⚠️  Database not found: {db_path}")
        print(f"   Database may already be deleted or never created.")
        print(f"\nNext step:")
        print(f"1. Start server to create new database: py start_server.py")


if __name__ == "__main__":
    clear_database()

