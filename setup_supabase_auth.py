import os
from dotenv import load_dotenv, set_key

def setup_supabase_auth():
    """Setup Supabase authentication configuration."""
    
    # Load existing environment variables
    load_dotenv("supabase.env")
    
    print("🔐 Supabase Auth Setup")
    print("=" * 50)
    
    current_url = os.getenv("SUPABASE_URL", "https://otiivelflvidgyfshmjn.supabase.co")
    current_jwt_secret = os.getenv("SUPABASE_JWT_SECRET", "not-set")
    
    print(f"Current Supabase URL: {current_url}")
    print(f"Current JWT Secret: {'Set' if current_jwt_secret != 'not-set' else 'Not Set'}")
    
    print("\n📋 To get your Supabase JWT Secret:")
    print("1. Go to https://supabase.com/dashboard")
    print("2. Select your project")
    print("3. Go to Settings > API")
    print("4. Copy the 'JWT Secret' value")
    
    if current_jwt_secret == 'not-set':
        jwt_secret = input("\nEnter your Supabase JWT Secret: ").strip()
        
        if jwt_secret:
            set_key("supabase.env", "SUPABASE_JWT_SECRET", jwt_secret)
            print("✅ JWT Secret updated successfully!")
        else:
            print("❌ No JWT Secret provided. Please update supabase.env manually.")
    else:
        print(f"\n✅ JWT Secret is already configured.")
        update = input("Do you want to update it? (y/N): ").strip().lower()
        
        if update == 'y':
            jwt_secret = input("Enter new JWT Secret: ").strip()
            if jwt_secret:
                set_key("supabase.env", "SUPABASE_JWT_SECRET", jwt_secret)
                print("✅ JWT Secret updated successfully!")
    
    print("\n🗄️  Database Setup:")
    print("1. Go to your Supabase project dashboard")
    print("2. Go to SQL Editor")
    print("3. Run the SQL script from 'database_setup.sql'")
    print("4. This will create the profiles table and triggers")
    
    print("\n🚀 Next Steps:")
    print("1. Update SUPABASE_JWT_SECRET in supabase.env (if not done)")
    print("2. Run the database_setup.sql script in Supabase")
    print("3. Start your FastAPI app: python run.py")
    print("4. Test authentication at: http://localhost:8000/docs")

if __name__ == "__main__":
    setup_supabase_auth()
