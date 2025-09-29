"""
Setup script for Enjaz integration.

This script helps set up the Enjaz integration by:
1. Generating encryption keys
2. Creating database tables
3. Validating configuration
"""

import asyncio
import os
import sys
from pathlib import Path

# Add the app directory to the Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.utils.encryption import generate_encryption_key
from app.db.database import create_tables
from app.config.enhanced_logging import setup_logging, get_logger

# Setup logging
setup_logging()
logger = get_logger(__name__)


def check_environment():
    """Check if required environment variables are set."""
    print("🔍 Checking environment configuration...")
    
    env_file = Path("supabase.env")
    if not env_file.exists():
        print("❌ supabase.env file not found!")
        print("📝 Please copy supabase.env.template to supabase.env and configure it.")
        return False
    
    # Check for encryption key
    from dotenv import load_dotenv
    load_dotenv("supabase.env")
    
    encryption_key = os.getenv("ENCRYPTION_KEY")
    if not encryption_key:
        print("⚠️  ENCRYPTION_KEY not found in environment")
        print("🔑 Generating new encryption key...")
        
        new_key = generate_encryption_key()
        print(f"📋 Add this to your supabase.env file:")
        print(f"ENCRYPTION_KEY={new_key}")
        return False
    
    print("✅ Environment configuration looks good!")
    return True


async def setup_database():
    """Set up database tables."""
    print("🗄️  Setting up database tables...")
    
    try:
        await create_tables()
        print("✅ Database tables created successfully!")
        return True
    except Exception as e:
        print(f"❌ Database setup failed: {str(e)}")
        return False


def check_dependencies():
    """Check if required dependencies are installed."""
    print("📦 Checking dependencies...")
    
    required_packages = [
        "cryptography",
        "playwright",
        "fastapi",
        "sqlalchemy",
        "pydantic"
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - not installed")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n📋 Install missing packages with:")
        print(f"pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ All dependencies are installed!")
    return True


def check_playwright_browsers():
    """Check if Playwright browsers are installed."""
    print("🌐 Checking Playwright browsers...")
    
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            try:
                browser = p.chromium.launch(headless=True)
                browser.close()
                print("✅ Chromium browser is available!")
                return True
            except Exception:
                print("❌ Chromium browser not found")
                print("📋 Install Playwright browsers with:")
                print("playwright install chromium")
                return False
                
    except ImportError:
        print("❌ Playwright not installed")
        return False


async def main():
    """Main setup function."""
    print("🚀 Setting up Enjaz Integration\n")
    
    # Check dependencies
    if not check_dependencies():
        print("\n❌ Setup failed: Missing dependencies")
        return
    
    print()
    
    # Check environment
    if not check_environment():
        print("\n❌ Setup failed: Environment configuration issues")
        return
    
    print()
    
    # Check Playwright browsers
    if not check_playwright_browsers():
        print("\n❌ Setup failed: Playwright browsers not installed")
        return
    
    print()
    
    # Set up database
    if not await setup_database():
        print("\n❌ Setup failed: Database setup issues")
        return
    
    print("\n🎉 Enjaz Integration setup completed successfully!")
    print("\n📋 Next steps:")
    print("1. Start the server: python -m uvicorn app.main:app --reload")
    print("2. Test the API: http://localhost:8000/docs")
    print("3. Run tests: python test_enjaz_integration.py")
    print("\n📖 For more information, see ENJAZ_INTEGRATION_README.md")


if __name__ == "__main__":
    asyncio.run(main())
