"""
Email service for sending verification emails.

This module handles SMTP email sending functionality,
following separation of concerns and dependency inversion.
"""

import asyncio
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional
import os
from datetime import datetime, timedelta
import secrets
import string

from ..config.logging_config import get_logger
from ..utils.exceptions import ExternalServiceException
from ..utils.api_exceptions import ApiException
from ..schemas.response import raise_error_response

logger = get_logger(__name__)


class EmailService:
    """
    Email service for sending verification emails via SMTP.
    
    This service handles all email-related operations including
    verification email sending and template rendering.
    """
    
    def __init__(self):
        # SMTP Configuration from environment variables
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_username)
        self.from_name = os.getenv("FROM_NAME", "Your App")
        
        # App configuration
        self.app_name = os.getenv("APP_NAME", "Your App")
        self.frontend_url = os.getenv("FRONTEND_URL", "http://localhost:3000")
        
        # Validate required configuration
        if not self.smtp_username or not self.smtp_password:
            logger.warning("SMTP credentials not configured. Email verification will be disabled.")
    
    def generate_verification_token(self, length: int = 32) -> str:
        """Generate a secure verification token."""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def create_verification_email_html(self, user_name: str, verification_token: str, verification_url: str) -> str:
        """Create HTML email template for verification."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Email Verification - {self.app_name}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .header {{
                    background-color: #4CAF50;
                    color: white;
                    padding: 20px;
                    text-align: center;
                    border-radius: 8px 8px 0 0;
                }}
                .content {{
                    background-color: #f9f9f9;
                    padding: 30px;
                    border-radius: 0 0 8px 8px;
                }}
                .button {{
                    display: inline-block;
                    background-color: #4CAF50;
                    color: white;
                    padding: 12px 30px;
                    text-decoration: none;
                    border-radius: 5px;
                    margin: 20px 0;
                }}
                .button:hover {{
                    background-color: #45a049;
                }}
                .footer {{
                    text-align: center;
                    margin-top: 30px;
                    font-size: 12px;
                    color: #666;
                }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{self.app_name}</h1>
                <h2>Email Verification Required</h2>
            </div>
            <div class="content">
                <p>Hello {user_name},</p>
                
                <p>Thank you for signing up with {self.app_name}! To complete your registration, please verify your email address by clicking the button below:</p>
                
                <div style="text-align: center;">
                    <a href="{verification_url}" class="button">Verify Email Address</a>
                </div>
                
                <p>If the button doesn't work, you can copy and paste this link into your browser:</p>
                <p style="word-break: break-all; background-color: #e9e9e9; padding: 10px; border-radius: 4px;">
                    {verification_url}
                </p>
                
                <p><strong>Important:</strong> This verification link will expire in 24 hours for security reasons.</p>
                
                <p>If you didn't create an account with {self.app_name}, please ignore this email.</p>
                
                <p>Best regards,<br>The {self.app_name} Team</p>
            </div>
            <div class="footer">
                <p>This is an automated message. Please do not reply to this email.</p>
                <p>&copy; 2024 {self.app_name}. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
    
    def create_verification_email_text(self, user_name: str, verification_token: str, verification_url: str) -> str:
        """Create plain text email template for verification."""
        return f"""
        Email Verification - {self.app_name}
        
        Hello {user_name},
        
        Thank you for signing up with {self.app_name}! To complete your registration, please verify your email address by visiting the following link:
        
        {verification_url}
        
        Important: This verification link will expire in 24 hours for security reasons.
        
        If you didn't create an account with {self.app_name}, please ignore this email.
        
        Best regards,
        The {self.app_name} Team
        
        ---
        This is an automated message. Please do not reply to this email.
        © 2024 {self.app_name}. All rights reserved.
        """
    
    async def send_verification_email(self, to_email: str, user_name: str, verification_token: str) -> bool:
        """
        Send verification email to user.
        
        Args:
            to_email: Recipient email address
            user_name: User's name for personalization
            verification_token: Verification token
            
        Returns:
            bool: True if email sent successfully, False otherwise
            
        Raises:
            ApiException: If email sending fails
        """
        try:
            if not self.smtp_username or not self.smtp_password:
                logger.warning("SMTP not configured, skipping email verification")
                return False
            
            # Create verification URL
            verification_url = f"{self.frontend_url}/verify-email?token={verification_token}"
            
            # Create email content
            html_content = self.create_verification_email_html(user_name, verification_token, verification_url)
            text_content = self.create_verification_email_text(user_name, verification_token, verification_url)
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = f"Verify Your Email - {self.app_name}"
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            
            # Add both HTML and text versions
            text_part = MIMEText(text_content, "plain")
            html_part = MIMEText(html_content, "html")
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Send email using asyncio
            await self._send_email_async(message, to_email)
            
            logger.info(f"Verification email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send verification email to {to_email}: {str(e)}")
            raise_error_response(
                status_code=500,
                message="Failed to send verification email",
                field="email"
            )
    
    async def _send_email_async(self, message: MIMEMultipart, to_email: str):
        """Send email asynchronously using asyncio."""
        def send_email():
            try:
                # Create secure connection
                context = ssl.create_default_context()
                
                # Connect to server
                with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                    server.starttls(context=context)
                    server.login(self.smtp_username, self.smtp_password)
                    
                    # Send email
                    text = message.as_string()
                    server.sendmail(self.from_email, to_email, text)
                    
            except Exception as e:
                logger.error(f"SMTP error: {str(e)}")
                raise ExternalServiceException(f"Email service error: {str(e)}")
        
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, send_email)
    
    def is_email_configured(self) -> bool:
        """Check if email service is properly configured."""
        return bool(self.smtp_username and self.smtp_password)
