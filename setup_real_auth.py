"""
Setup script for real Supabase authentication
Run this to configure your environment variables
"""

import os
from pathlib import Path

def setup_supabase_auth():
    """Setup Supabase authentication environment variables"""
    
    print("🔧 Setting up Real Supabase Authentication")
    print("=" * 50)
    
    # Check if .env file exists
    env_file = Path(".env")
    if not env_file.exists():
        print("📝 Creating .env file...")
        env_file.touch()
    
    # Read existing .env content
    env_content = ""
    if env_file.exists():
        with open(env_file, "r") as f:
            env_content = f.read()
    
    # Required environment variables
    required_vars = {
        "SUPABASE_URL": "https://otiivelflvidgyfshmjn.supabase.co",
        "SUPABASE_ANON_KEY": "YOUR_SUPABASE_ANON_KEY_HERE",
        "SUPABASE_JWT_SECRET": "YOUR_SUPABASE_JWT_SECRET_HERE"
    }
    
    print("\n📋 Required Environment Variables:")
    for var, default in required_vars.items():
        current_value = os.getenv(var)
        if current_value and current_value != default:
            print(f"✅ {var}: {current_value[:20]}...")
        else:
            print(f"❌ {var}: Not set")
    
    print("\n🔑 How to get your Supabase credentials:")
    print("1. Go to your Supabase Dashboard")
    print("2. Select your project")
    print("3. Go to Settings > API")
    print("4. Copy the following values:")
    print("   - Project URL → SUPABASE_URL")
    print("   - anon public → SUPABASE_ANON_KEY")
    print("   - JWT Secret → SUPABASE_JWT_SECRET")
    
    print("\n📝 Add these to your .env file:")
    print("-" * 30)
    for var, default in required_vars.items():
        if var not in env_content:
            print(f"{var}={default}")
    print("-" * 30)
    
    print("\n👤 Create test user in Supabase:")
    print("1. Go to Authentication > Users")
    print("2. Click 'Add user'")
    print("3. Email: mohammed211920@gmail.com")
    print("4. Password: password123")
    print("5. Click 'Create user'")
    
    print("\n🚀 Test endpoints:")
    print("POST /api/v1/supabase-auth/signin/mohammed")
    print("GET /api/v1/supabase-auth/user")
    print("GET /api/v1/subscriptions/status")
    
    print("\n✨ Setup complete! Restart your server after updating .env")

if __name__ == "__main__":
    setup_supabase_auth()

