#!/usr/bin/env python3
"""
Setup script for Supabase configuration
"""
import os
from dotenv import load_dotenv

def setup_supabase():
    """Setup Supabase configuration with user input."""
    print("🚀 Supabase Setup")
    print("=" * 50)
    
    # Load existing environment
    load_dotenv("supabase.env")
    
    # Get current values
    current_url = os.getenv("SUPABASE_URL", "https://otiivelflvidgyfshmjn.supabase.co")
    current_anon_key = os.getenv("SUPABASE_ANON_KEY", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im90aWl2ZWxmbHZpZGd5ZnNobWpuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE4NTQ2MDksImV4cCI6MjA2NzQzMDYwOX0.aoJZdCUfLngPLO0uDoYHp3GdiQpZlf5PlEZlr2BIr1g")
    
    print(f"Current Supabase URL: {current_url}")
    print(f"Current ANON Key: {current_anon_key[:20]}...")
    print()
    
    # Get database password
    print("🔐 Database Password Required")
    print("You need to get your database password from Supabase:")
    print("1. Go to https://supabase.com/dashboard")
    print("2. Select your project: otiivelflvidgyfshmjn")
    print("3. Go to Settings > Database")
    print("4. Find your database password")
    print()
    
    db_password = input("Enter your database password: ").strip()
    
    if not db_password:
        print("❌ Database password is required!")
        return
    
    # Create database URL
    database_url = f"postgresql+asyncpg://postgres:{db_password}@db.otiivelflvidgyfshmjn.supabase.co:5432/postgres"
    
    # Update environment file
    env_content = f"""# Supabase Configuration
SUPABASE_URL=https://otiivelflvidgyfshmjn.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im90aWl2ZWxmbHZpZGd5ZnNobWpuIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE4NTQ2MDksImV4cCI6MjA2NzQzMDYwOX0.aoJZdCUfLngPLO0uDoYHp3GdiQpZlf5PlEZlr2BIr1g

# Database Configuration (Supabase PostgreSQL)
DATABASE_URL={database_url}

# JWT Secret Key
SECRET_KEY=your-super-secret-jwt-key-change-in-production

# Environment
ENVIRONMENT=development
"""
    
    with open("supabase.env", "w") as f:
        f.write(env_content)
    
    print("✅ Environment configuration updated!")
    print("✅ Ready to connect to Supabase PostgreSQL")
    print()
    print("Next steps:")
    print("1. Run: python run.py")
    print("2. Test your API at: http://localhost:8000/docs")

if __name__ == "__main__":
    setup_supabase()
