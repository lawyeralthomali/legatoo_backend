#!/usr/bin/env python3
"""
Email URL Configuration Fix Script

This script helps diagnose and fix the email verification URL issue
where URLs are being generated as localhost instead of production URLs.

Run this script on your production server to check the configuration.
"""

import os
import sys
import logging

# Setup basic logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def check_environment_variables():
    """Check if required environment variables are set."""
    logger.info("🔍 Checking environment variables...")
    
    critical_vars = {
        'ENVIRONMENT': 'production',
        'FRONTEND_URL': 'https://legatoo.westlinktowing.com',
        'BACKEND_URL': 'https://api.westlinktowing.com',
    }
    
    all_good = True
    for var, expected_prefix in critical_vars.items():
        value = os.getenv(var, 'NOT_SET')
        logger.info(f"  {var}: {value}")
        
        if value == 'NOT_SET':
            logger.warning(f"❌ {var} is not set!")
            all_good = False
        elif var in ['FRONTEND_URL', 'BACKEND_URL'] and not value.startswith(expected_prefix):
            logger.warning(f"⚠️  {var} ({value}) doesn't start with expected prefix ({expected_prefix})")
    
    return all_good

def test_url_configuration():
    """Test the URL configuration."""
    logger.info("🧪 Testing URL configuration...")
    
    try:
        # Add the app directory to the Python path
        sys.path.insert(0, '.')
        
        from app.config.urls import get_url_config
        
        url_config = get_url_config()
        
        logger.info("URL Configuration Results:")
        logger.info(f"  Environment: {url_config.environment}")
        logger.info(f"  Frontend URL: {url_config.frontend_url}")
        logger.info(f"  Backend URL: {url_config.backend_url}")
        logger.info(f"  Email Base URL: {url_config.email_base_url}")
        
        # Test verification URL generation
        test_token = "test-verification-token-123"
        verification_url = url_config.get_verification_url(test_token)
        logger.info(f"  Verification URL example: {verification_url}")
        
        # Check if URLs are production-ready
        is_production_ready = (
            url_config.frontend_url.startswith("https://legatoo.westlinktowing.com") and
            url_config.backend_url.startswith("https://api.westlinktowing.com") and
            verification_url.startswith("https://api.westlinktowing.com")
        )
        
        if is_production_ready:
            logger.info("✅ URL configuration is production-ready!")
            return True
        else:
            logger.error("❌ URL configuration is not production-ready!")
            logger.error("Email verification will use localhost URLs instead of production URLs")
            return False
            
    except Exception as e:
        logger.error(f"❌ Failed to test URL configuration: {str(e)}")
        return False

def suggest_fixes():
    """Suggest fixes for the configuration issues."""
    logger.info("💡 Suggestions to fix the email URL issue:")
    logger.info("")
    logger.info("1. Set these environment variables in your production deployment:")
    logger.info("   export ENVIRONMENT=production")
    logger.info("   export FRONTEND_URL=https://legatoo.westlinktowing.com")
    logger.info("   export BACKEND_URL=https://api.westlinktowing.com")
    logger.info("")
    logger.info("2. Or create a .env file in your project root with:")
    logger.info("   ENVIRONMENT=production")
    logger.info("   FRONTEND_URL=https://legatoo.westlinktowing.com")
    logger.info("   BACKEND_URL=https://api.westlinktowing.com")
    logger.info("   SMTP_SERVER=smtp.hostinger.com")
    logger.info("   SMTP_PORT=587")
    logger.info("   SMTP_USERNAME=legatoo@althomalilawfirm.sa")
    logger.info("   SMTP_PASSWORD=your-smtp-password")
    logger.info("   FROM_EMAIL=legatoo@althomalilawfirm.sa")
    logger.info("   FROM_NAME=Legatoo App")
    logger.info("")
    logger.info("3. Restart your application after setting the environment variables")
    logger.info("")
    logger.info("4. Test the fix by visiting: https://api.westlinktowing.com/debug-urls")

def main():
    """Main function to run all checks."""
    logger.info("🚀 Starting email URL configuration diagnosis...")
    logger.info("=" * 60)
    
    env_check = check_environment_variables()
    url_check = test_url_configuration()
    
    logger.info("=" * 60)
    if env_check and url_check:
        logger.info("🎉 All checks passed! Email URLs should be working correctly.")
    else:
        logger.info("🔧 Configuration issues found. See suggestions below:")
        suggest_fixes()
    
    logger.info("=" * 60)
    logger.info("✅ Diagnosis complete!")

if __name__ == "__main__":
    main()
