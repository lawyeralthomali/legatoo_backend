#!/usr/bin/env python3
"""
Test script for email verification functionality.
"""
import asyncio
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv("supabase.env")

async def test_email_service():
    """Test email service functionality."""
    print("Testing Email Service...")
    
    try:
        from app.services.email_service import EmailService
        
        email_service = EmailService()
        
        # Check if email is configured
        if not email_service.is_email_configured():
            print("❌ Email service not configured. Please set SMTP credentials in supabase.env")
            print("\nRequired environment variables:")
            print("- SMTP_USERNAME")
            print("- SMTP_PASSWORD")
            print("- FROM_EMAIL")
            print("- FROM_NAME")
            return
        
        print("✅ Email service configured")
        
        # Generate test token
        token = email_service.generate_verification_token()
        print(f"✅ Generated verification token: {token[:10]}...")
        
        # Test email template
        html_content = email_service.create_verification_email_html(
            "Test User", token, f"http://localhost:3000/verify-email?token={token}"
        )
        print("✅ Email template generated")
        
        # Test sending email (uncomment to actually send)
        # await email_service.send_verification_email(
        #     to_email="test@example.com",
        #     user_name="Test User",
        #     verification_token=token
        # )
        # print("✅ Test email sent")
        
        print("\n🎉 Email service test completed!")
        
    except Exception as e:
        print(f"❌ Error testing email service: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_email_service())
