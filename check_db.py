#!/usr/bin/env python3
"""
Script to check SQLite database contents.
"""
import sqlite3
import os

def check_database():
    db_path = "app.db"
    
    if not os.path.exists(db_path):
        print("❌ Database file 'app.db' does not exist")
        return
    
    print(f"✅ Database file exists: {os.path.abspath(db_path)}")
    print(f"📁 File size: {os.path.getsize(db_path)} bytes")
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get all tables
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()
        
        print(f"\n📋 Tables in database ({len(tables)} total):")
        for table in tables:
            print(f"  - {table[0]}")
        
        # Check if users and profiles tables exist
        if ('users',) in tables:
            cursor.execute("SELECT COUNT(*) FROM users;")
            user_count = cursor.fetchone()[0]
            print(f"\n👥 Users table: {user_count} records")
        
        if ('profiles',) in tables:
            cursor.execute("SELECT COUNT(*) FROM profiles;")
            profile_count = cursor.fetchone()[0]
            print(f"👤 Profiles table: {profile_count} records")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Error checking database: {e}")

if __name__ == "__main__":
    check_database()
