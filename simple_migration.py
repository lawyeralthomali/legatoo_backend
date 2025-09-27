#!/usr/bin/env python3
"""
Simple database migration script to add email verification fields.
"""
import sqlite3
import os

def migrate_database():
    """Add verification fields to users table."""
    db_path = "app.db"
    
    if not os.path.exists(db_path):
        print("❌ Database file 'app.db' does not exist")
        return
    
    print("Adding email verification fields to users table...")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(users)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'verification_token' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN verification_token VARCHAR(255)")
            print("✅ Added verification_token column")
        else:
            print("✅ verification_token column already exists")
        
        if 'verification_token_expires' not in columns:
            cursor.execute("ALTER TABLE users ADD COLUMN verification_token_expires DATETIME")
            print("✅ Added verification_token_expires column")
        else:
            print("✅ verification_token_expires column already exists")
        
        # Create index on verification_token
        try:
            cursor.execute("CREATE INDEX IF NOT EXISTS ix_users_verification_token ON users(verification_token)")
            print("✅ Created index on verification_token")
        except sqlite3.OperationalError:
            print("✅ Index already exists")
        
        conn.commit()
        conn.close()
        
        print("\n🎉 Migration completed successfully!")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    migrate_database()
