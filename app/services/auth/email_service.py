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

from ...config.enhanced_logging import get_logger
from ...config.urls import get_url_config
from ...utils.exceptions import ExternalServiceException
from ...utils.api_exceptions import ApiException
from ...schemas.response import raise_error_response

logger = get_logger(__name__)


class EmailService:
    """
    Email service for sending verification emails via SMTP.
    
    This service handles all email-related operations including
    verification email sending and template rendering.
    """
    
    def __init__(self):
        # Get centralized URL configuration
        self.url_config = get_url_config()
        
        # SMTP Configuration from environment variables
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL", self.smtp_username)
        self.from_name = os.getenv("FROM_NAME", "Legatoo")
        
        # App configuration
        self.app_name = os.getenv("APP_NAME", "Legatoo")
        
        # Frontend URL for email links
        self.frontend_url = self.url_config.frontend_url
        
        # Validate required configuration
        if not self.smtp_username or not self.smtp_password:
            logger.warning("SMTP credentials not configured. Email verification will be disabled.")
    
    def generate_verification_token(self, length: int = 32) -> str:
        """Generate a secure verification token."""
        alphabet = string.ascii_letters + string.digits
        return ''.join(secrets.choice(alphabet) for _ in range(length))
    
    def create_verification_email_html(self, user_name: str, verification_token: str, verification_url: str, language: str = "bilingual") -> str:
        """Create HTML email template for verification."""
        if language == "bilingual":
            return self.create_verification_email_html_bilingual(user_name, verification_token, verification_url)
        elif language == "ar":
            return self.create_verification_email_html_arabic(user_name, verification_token, verification_url)
        else:
            return self.create_verification_email_html_english(user_name, verification_token, verification_url)
    
    def create_verification_email_html_bilingual(self, user_name: str, verification_token: str, verification_url: str) -> str:
        """Create bilingual HTML email template for verification (Arabic + English)."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Email Verification - Legatoo</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: 'Inter', 'Cairo', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #1a1a1a;
                    background-color: #f8fafc;
                    padding: 20px;
                }}
              
                .email-container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 24px;
                    box-shadow: 0 32px 64px rgba(0, 0, 0, 0.12);
                    overflow: hidden;
                }}
                .header {{
                    background:#679594;
                    color: white !important;
                    padding: 40px 30px;
                    text-align: center;
                    position: relative;
                }}
                .header::before {{
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    height: 6px;
                    background: linear-gradient(90deg, #667eea, #764ba2);
                }}
                .logo {{
                    width: 180px;
                    height: auto;
                    background: rgba(255, 255, 255, 0.2);
                    border-radius: 20px;
                    margin: 0 auto 20px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    backdrop-filter: blur(10px);
                    overflow: hidden;
                }}
                .logo img {{
                    width: 100%;
                    height: 100%;
                    object-fit: contain;
                }}
                .brand-name {{
                    font-size: 32px;
                    font-weight: 700;
                    margin-bottom: 8px;
                    letter-spacing: -0.5px;
                }}
                .tagline {{
                    font-size: 16px;
                    opacity: 0.9;
                    font-weight: 400;
                }}
                .content {{
                    padding: 40px 30px;
                }}
                .language-section {{
                    margin-bottom: 40px;
                    padding-bottom: 30px;
                    border-bottom: 2px solid #f1f5f9;
                }}
                .language-section:last-child {{
                    border-bottom: none;
                    margin-bottom: 0;
                }}
                .language-header {{
                    font-size: 20px;
                    font-weight: 700;
                    color: #679594;
                    margin-bottom: 20px;
                    text-align: center;
                    padding: 10px;
                    background: #f8fafc;
                    border-radius: 8px;
                }}
                .arabic-content {{
                    direction: rtl;
                    text-align: right;
                    font-family: 'Cairo', 'Tajawal', 'Segoe UI', sans-serif;
                }}
                .english-content {{
                    direction: ltr;
                    text-align: left;
                }}
                .greeting {{
                    font-size: 18px;
                    font-weight: 600;
                    color: #1a1a1a;
                    margin-bottom: 20px;
                }}
                .message {{
                    font-size: 16px;
                    color: #6b7280;
                    margin-bottom: 30px;
                    line-height: 1.7;
                }}
                .button-container {{
                    text-align: center;
                    margin: 30px 0;
                }}
                .button {{
                    display: inline-block;
                    background: #679594;
                    color: white !important;
                    padding: 16px 32px;
                    text-decoration: none;
                    border-radius: 12px;
                    font-weight: 600;
                    font-size: 16px;
                    box-shadow: 0 4px 16px rgba(102, 126, 234, 0.3);
                    transition: all 0.2s ease;
                }}
                .button:hover {{
                    transform: translateY(-1px);
                    box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
                }}
                .link-fallback {{
                    background: #f8fafc;
                    border: 1px solid #e2e8f0;
                    border-radius: 12px;
                    padding: 20px;
                    margin: 20px 0;
                    font-size: 14px;
                    color: #6b7280;
                }}
                .link-fallback strong {{
                    color: #374151;
                    display: block;
                    margin-bottom: 8px;
                }}
                .link-text {{
                    word-break: break-all;
                   
                    padding: 12px;
                    border-radius: 8px;
                    font-family: monospace;
                    font-size: 13px;
                }}
                .important {{
                    background: #fef3c7;
                    border: 1px solid #f59e0b;
                    border-radius: 12px;
                    padding: 16px;
                    margin: 20px 0;
                    font-size: 14px;
                    color: #92400e;
                }}
                .important strong {{
                    color: #78350f;
                }}
                .signature {{
                    margin-top: 30px;
                    font-size: 16px;
                    color: #374151;
                }}
                .footer {{
                    background: #f8fafc;
                    padding: 30px;
                    text-align: center;
                    border-top: 1px solid #e2e8f0;
                }}
                .footer p {{
                    font-size: 12px;
                    color: #9ca3af;
                    margin-bottom: 8px;
                }}
                @media (max-width: 600px) {{
                    .email-container {{
                        margin: 10px;
                        border-radius: 16px;
                    }}
                    .header, .content, .footer {{
                        padding: 30px 20px;
                    }}
                    .brand-name {{
                        font-size: 28px;
                    }}
                }}
            a {{
                    text-decoration: none;
                    color: #18295b;

                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <div class="logo">
                        <img src="https://legatoo.fastestfranchise.net/logo.png" alt="Legatoo Logo">
                    </div>
                    <div class="brand-name">Legatoo</div>
                    <div class="tagline">Your Legal Assistant | مساعدك القانوني</div>
                </div>
                <div class="content">
                    <!-- Arabic Section -->
                    <div class="language-section arabic-content">
                        <div class="language-header">العربية</div>
                        <div class="greeting">مرحباً {user_name}،</div>
                        
                        <div class="message">
                            شكراً لك على التسجيل في Legatoo! نحن متحمسون لانضمامك إلى منصتنا القانونية. لإكمال تسجيلك والبدء في استخدام خدماتنا، يرجى تأكيد عنوان بريدك الإلكتروني بالنقر على الزر أدناه.
                        </div>
                        
                        <div class="button-container">
                            <a href="{verification_url}" class="button">تأكيد البريد الإلكتروني</a>
                        </div>
                        
                        <div class="link-fallback">
                            <strong>الزر لا يعمل؟</strong>
                            انسخ والصق هذا الرابط في متصفحك:
                            <div class="link-text">{verification_url}</div>
                        </div>
                        
                        <div class="important">
                            <strong>إشعار أمني:</strong> ستنتهي صلاحية رابط التأكيد هذا خلال 24 ساعة لأمانك. إذا لم تقم بإنشاء حساب في Legatoo، يرجى تجاهل هذا البريد الإلكتروني.
                        </div>
                        
                        <div class="signature">
                            مع أطيب التحيات،<br>
                            فريق Legatoo
                        </div>
                    </div>
                    
                    <!-- English Section -->
                    <div class="language-section english-content">
                        <div class="language-header">English</div>
                        <div class="greeting">Hello {user_name},</div>
                        
                        <div class="message">
                            Thank you for signing up with Legatoo! We're excited to have you join our legal assistant platform. To complete your registration and start using our services, please verify your email address by clicking the button below.
                        </div>
                        
                        <div class="button-container">
                            <a href="{verification_url}" class="button">Verify Email Address</a>
                        </div>
                        
                        <div class="link-fallback">
                            <strong>Button not working?</strong>
                            Copy and paste this link into your browser:
                            <div class="link-text">{verification_url}</div>
                        </div>
                        
                        <div class="important">
                            <strong>Security Notice:</strong> This verification link will expire in 24 hours for your security. If you didn't create an account with Legatoo, please ignore this email.
                        </div>
                        
                        <div class="signature">
                            Best regards,<br>
                            The Legatoo Team
                        </div>
                    </div>
                </div>
                <div class="footer">
                    <p>This is an automated message. Please do not reply to this email.</p>
                    <p>هذه رسالة آلية. يرجى عدم الرد على هذا البريد الإلكتروني.</p>
                    <p>&copy; 2024 Legatoo. All rights reserved.</p>
                    <p>&copy; 2024 Legatoo. جميع الحقوق محفوظة.</p>
                    <p>Your trusted legal assistant platform | منصتك القانونية الموثوقة</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def create_verification_email_html_english(self, user_name: str, verification_token: str, verification_url: str) -> str:
        """Create English-only HTML email template for verification."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Email Verification - Legatoo</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #1a1a1a;
                    background-color: #f8fafc;
                    padding: 20px;
                }}
                .email-container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 24px;
                    box-shadow: 0 32px 64px rgba(0, 0, 0, 0.12);
                    overflow: hidden;
                }}
                .header {{
                    background: #679594;
                    color: white;
                    padding: 40px 30px;
                    text-align: center;
                    position: relative;
                }}
          
                .header::before {{
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    height: 6px;
                    background: #679594;
                }}
                .logo {{
                    width: 180px;
                    height:auto;
              
                    border-radius: 20px;
                    margin: 0 auto 20px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    backdrop-filter: blur(10px);
                    overflow: hidden;
                }}
                .logo img {{
                    width: 100%;
                    height: 100%;
                    object-fit: contain;
                }}
                .brand-name {{
                    font-size: 32px;
                    font-weight: 700;
                    margin-bottom: 8px;
                    letter-spacing: -0.5px;
                }}
                .tagline {{
                    font-size: 16px;
                    opacity: 0.9;
                    font-weight: 400;
                }}
                .content {{
                    padding: 40px 30px;
                }}
                .greeting {{
                    font-size: 18px;
                    font-weight: 600;
                    color: #1a1a1a;
                    margin-bottom: 20px;
                }}
                .message {{
                    font-size: 16px;
                    color: #6b7280;
                    margin-bottom: 30px;
                    line-height: 1.7;
                }}
                .button-container {{
                    text-align: center;
                    margin: 30px 0;
                }}
                .button {{
                    display: inline-block;
                    background:#679594;
                    color: white !important;
                    padding: 16px 32px;
                    text-decoration: none;
                    border-radius: 12px;
                    font-weight: 600;
                    font-size: 16px;
                    box-shadow: 0 4px 16px rgba(24, 41, 91, 0.3);
                    transition: all 0.2s ease;
                }}
                .button:hover {{
                    transform: translateY(-1px);
                    box-shadow: 0 8px 24px rgba(24, 41, 91, 0.4);
                }}
                .link-fallback {{
                
                    border: 1px solid #e2e8f0;
                    border-radius: 12px;
                    padding: 20px;
                    margin: 20px 0;
                    font-size: 14px;
                    color: #6b7280;
                }}
                .link-fallback strong {{
                    color: #374151;
                    display: block;
                    margin-bottom: 8px;
                }}
             
                .link-text {{
                    word-break: break-all;
                  
                    padding: 12px;
                    border-radius: 8px;
                    font-family: monospace;
                    font-size: 13px;
                }}
                .important {{
                    background: #fef3c7;
                    border: 1px solid #f59e0b;
                    border-radius: 12px;
                    padding: 16px;
                    margin: 20px 0;
                    font-size: 14px;
                    color: #92400e;
                }}
                .important strong {{
                    color: #78350f;
                }}
                .signature {{
                    margin-top: 30px;
                    font-size: 16px;
                    color: #374151;
                }}
                .footer {{
                    background: #f8fafc;
                    padding: 30px;
                    text-align: center;
                    border-top: 1px solid #e2e8f0;
                }}
                .footer p {{
                    font-size: 12px;
                    color: #9ca3af;
                    margin-bottom: 8px;
                }}
                @media (max-width: 600px) {{
                    .email-container {{
                        margin: 10px;
                        border-radius: 16px;
                    }}
                    .header, .content, .footer {{
                        padding: 30px 20px;
                    }}
                    .brand-name {{
                        font-size: 28px;
                    }}
                }}
              a {{
                    text-decoration: none;
                    color: #18295b;

                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <div class="logo">
                        <img src="https://legatoo.fastestfranchise.net/logo.png" alt="Legatoo Logo">
                    </div>
                    <div class="brand-name">Legatoo</div>
                    <div class="tagline">Your Legal Assistant</div>
                </div>
                <div class="content">
                    <div class="greeting">Hello {user_name},</div>
                    
                    <div class="message">
                        Thank you for signing up with Legatoo! We're excited to have you join our legal assistant platform. To complete your registration and start using our services, please verify your email address by clicking the button below.
                    </div>
                    
                    <div class="button-container">
                        <a href="{verification_url}" class="button">Verify Email Address</a>
                    </div>
                    
                    <div class="link-fallback">
                        <strong>Button not working?</strong>
                        Copy and paste this link into your browser:
                        <div class="link-text">{verification_url}</div>
                    </div>
                    
                    <div class="important">
                        <strong>Security Notice:</strong> This verification link will expire in 24 hours for your security. If you didn't create an account with Legatoo, please ignore this email.
                    </div>
                    
                    <div class="signature">
                        Best regards,<br>
                        The Legatoo Team
                    </div>
                </div>
                <div class="footer">
                    <p>This is an automated message. Please do not reply to this email.</p>
                    <p>&copy; 2024 Legatoo. All rights reserved.</p>
                    <p>Your trusted legal assistant platform</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def create_verification_email_html_arabic(self, user_name: str, verification_token: str, verification_url: str) -> str:
        """Create Arabic-only HTML email template for verification."""
        return f"""
        <!DOCTYPE html>
        <html dir="rtl" lang="ar">
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>تأكيد البريد الإلكتروني - Legatoo</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: 'Cairo', 'Tajawal', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #1a1a1a;
                    background-color: #f8fafc;
                    padding: 20px;
                    direction: rtl;
                }}
                .email-container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 24px;
                    box-shadow: 0 32px 64px rgba(0, 0, 0, 0.12);
                    overflow: hidden;
                }}
                .header {{
                    background: #679594;
                    color: white;
                    padding: 40px 30px;
                    text-align: center;
                    position: relative;
                }}
                .header::before {{
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    height: 6px;
                    background: #679594;
                }}
                .logo {{
                    width: 180px;
                    height: auto;
                    background: rgba(255, 255, 255, 0.2);
                    border-radius: 20px;
                    margin: 0 auto 20px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    backdrop-filter: blur(10px);
                    overflow: hidden;
                }}
                .logo img {{
                    width: 100%;
                    height: 100%;
                    object-fit: contain;
                }}
                .brand-name {{
                    font-size: 32px;
                    font-weight: 700;
                    margin-bottom: 8px;
                    letter-spacing: -0.5px;
                }}
                .tagline {{
                    font-size: 16px;
                    opacity: 0.9;
                    font-weight: 400;
                }}
                .content {{
                    padding: 40px 30px;
                }}
                .greeting {{
                    font-size: 18px;
                    font-weight: 600;
                    color: #1a1a1a;
                    margin-bottom: 20px;
                }}
                .message {{
                    font-size: 16px;
                    color: #6b7280;
                    margin-bottom: 30px;
                    line-height: 1.7;
                }}
                .button-container {{
                    text-align: center;
                    margin: 30px 0;
                }}
                .button {{
                    display: inline-block;
                    background: #679594;
                    color: white !important;
                    padding: 16px 32px;
                    text-decoration: none;
                    border-radius: 12px;
                    font-weight: 600;
                    font-size: 16px;
                    box-shadow: 0 4px 16px rgba(24, 41, 91, 0.3);
                    transition: all 0.2s ease;
                }}
                .button:hover {{
                    transform: translateY(-1px);
                    box-shadow: 0 8px 24px rgba(24, 41, 91, 0.4);
                }}
                .link-fallback {{
               
                    border: 1px solid #e2e8f0;
                    border-radius: 12px;
                    padding: 20px;
                    margin: 20px 0;
                    font-size: 14px;
                    color: #6b7280;
                }}
                .link-fallback strong {{
                    color: black;
                    display: block;
                    margin-bottom: 8px;
                }}
                .link-text {{
                    word-break: break-all;
                
                    padding: 12px;
                    border-radius: 8px;
                    font-family: monospace;
                    font-size: 13px;
                }}
                .important {{
                    background: #fef3c7;
                    border: 1px solid #f59e0b;
                    border-radius: 12px;
                    padding: 16px;
                    margin: 20px 0;
                    font-size: 14px;
                    color: #92400e;
                }}
                .important strong {{
                    color: #78350f;
                }}
                .signature {{
                    margin-top: 30px;
                    font-size: 16px;
                    color: #374151;
                }}
                .footer {{
                    background: #f8fafc;
                    padding: 30px;
                    text-align: center;
                    border-top: 1px solid #e2e8f0;
                }}
                .footer p {{
                    font-size: 12px;
                    color: #9ca3af;
                    margin-bottom: 8px;
                }}
                @media (max-width: 600px) {{
                    .email-container {{
                        margin: 10px;
                        border-radius: 16px;
                    }}
                    .header, .content, .footer {{
                        padding: 30px 20px;
                    }}
                    .brand-name {{
                        font-size: 28px;
                    }}
                }}
               a {{
                    text-decoration: none;
                    color: #18295b;

                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <div class="logo">
                        <img src="https://legatoo.fastestfranchise.net/logo.png" alt="Legatoo Logo">
                    </div>
                    <div class="brand-name">Legatoo</div>
                    <div class="tagline">مساعدك القانوني</div>
                </div>
                <div class="content">
                    <div class="greeting">مرحباً {user_name}،</div>
                    
                    <div class="message">
                        شكراً لك على التسجيل في Legatoo! نحن متحمسون لانضمامك إلى منصتنا القانونية. لإكمال تسجيلك والبدء في استخدام خدماتنا، يرجى تأكيد عنوان بريدك الإلكتروني بالنقر على الزر أدناه.
                    </div>
                    
                    <div class="button-container">
                        <a href="{verification_url}" class="button">تأكيد البريد الإلكتروني</a>
                    </div>
                    
                    <div class="link-fallback">
                        <strong>الزر لا يعمل؟</strong>
                        انسخ والصق هذا الرابط في متصفحك:
                        <div class="link-text">{verification_url}</div>
                    </div>
                    
                    <div class="important">
                        <strong>إشعار أمني:</strong> ستنتهي صلاحية رابط التأكيد هذا خلال 24 ساعة لأمانك. إذا لم تقم بإنشاء حساب في Legatoo، يرجى تجاهل هذا البريد الإلكتروني.
                    </div>
                    
                    <div class="signature">
                        مع أطيب التحيات،<br>
                        فريق Legatoo
                    </div>
                </div>
                <div class="footer">
                    <p>هذه رسالة آلية. يرجى عدم الرد على هذا البريد الإلكتروني.</p>
                    <p>&copy; 2024 Legatoo. جميع الحقوق محفوظة.</p>
                    <p>منصتك القانونية الموثوقة</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def create_verification_email_text(self, user_name: str, verification_token: str, verification_url: str, language: str = "bilingual") -> str:
        """Create plain text email template for verification."""
        if language == "bilingual":
            return self.create_verification_email_text_bilingual(user_name, verification_token, verification_url)
        elif language == "ar":
            return self.create_verification_email_text_arabic(user_name, verification_token, verification_url)
        else:
            return self.create_verification_email_text_english(user_name, verification_token, verification_url)
    
    def create_verification_email_text_bilingual(self, user_name: str, verification_token: str, verification_url: str) -> str:
        """Create bilingual plain text email template for verification."""
        return f"""
Email Verification - Legatoo | تأكيد البريد الإلكتروني - Legatoo

العربية:
مرحباً {user_name}،

شكراً لك على التسجيل في Legatoo! نحن متحمسون لانضمامك إلى منصتنا القانونية. لإكمال تسجيلك والبدء في استخدام خدماتنا، يرجى تأكيد عنوان بريدك الإلكتروني بزيارة الرابط التالي:

{verification_url}

إشعار أمني: ستنتهي صلاحية رابط التأكيد هذا خلال 24 ساعة لأمانك.

إذا لم تقم بإنشاء حساب في Legatoo، يرجى تجاهل هذا البريد الإلكتروني.

مع أطيب التحيات،
فريق Legatoo

---
English:
Hello {user_name},

Thank you for signing up with Legatoo! We're excited to have you join our legal assistant platform. To complete your registration and start using our services, please verify your email address by visiting the following link:

{verification_url}

Security Notice: This verification link will expire in 24 hours for your security.

If you didn't create an account with Legatoo, please ignore this email.

Best regards,
The Legatoo Team

---
This is an automated message. Please do not reply to this email.
هذه رسالة آلية. يرجى عدم الرد على هذا البريد الإلكتروني.
© 2024 Legatoo. All rights reserved. | جميع الحقوق محفوظة.
Your trusted legal assistant platform | منصتك القانونية الموثوقة
        """
    
    def create_verification_email_text_english(self, user_name: str, verification_token: str, verification_url: str) -> str:
        """Create English plain text email template for verification."""
        return f"""
Email Verification - Legatoo

Hello {user_name},

Thank you for signing up with Legatoo! We're excited to have you join our legal assistant platform. To complete your registration and start using our services, please verify your email address by visiting the following link:

{verification_url}

Security Notice: This verification link will expire in 24 hours for your security.

If you didn't create an account with Legatoo, please ignore this email.

Best regards,
The Legatoo Team

---
This is an automated message. Please do not reply to this email.
© 2024 Legatoo. All rights reserved.
Your trusted legal assistant platform
        """
    
    def create_verification_email_text_arabic(self, user_name: str, verification_token: str, verification_url: str) -> str:
        """Create Arabic plain text email template for verification."""
        return f"""
تأكيد البريد الإلكتروني - Legatoo

مرحباً {user_name}،

شكراً لك على التسجيل في Legatoo! نحن متحمسون لانضمامك إلى منصتنا القانونية. لإكمال تسجيلك والبدء في استخدام خدماتنا، يرجى تأكيد عنوان بريدك الإلكتروني بزيارة الرابط التالي:

{verification_url}

إشعار أمني: ستنتهي صلاحية رابط التأكيد هذا خلال 24 ساعة لأمانك.

إذا لم تقم بإنشاء حساب في Legatoo، يرجى تجاهل هذا البريد الإلكتروني.

مع أطيب التحيات،
فريق Legatoo

---
هذه رسالة آلية. يرجى عدم الرد على هذا البريد الإلكتروني.
© 2024 Legatoo. جميع الحقوق محفوظة.
منصتك القانونية الموثوقة
        """
    
    async def send_verification_email(self, to_email: str, user_name: str, verification_token: str, language: str = "bilingual") -> bool:
        """
        Send verification email to user.
        
        Args:
            to_email: Recipient email address
            user_name: User's name for personalization
            verification_token: Verification token
            language: Language code ("en", "ar", or "bilingual")
            
        Returns:
            bool: True if email sent successfully, False otherwise
            
        Raises:
            ApiException: If email sending fails
        """
        try:
            if not self.smtp_username or not self.smtp_password:
                logger.warning("SMTP not configured, skipping email verification")
                return False
            
            # Create verification URL using centralized config
            verification_url = self.url_config.get_verification_url(verification_token)
            
            # Create email content
            html_content = self.create_verification_email_html(user_name, verification_token, verification_url, language)
            text_content = self.create_verification_email_text(user_name, verification_token, verification_url, language)
            
            # Create message
            message = MIMEMultipart("alternative")
            if language == "ar":
                subject = "تأكيد البريد الإلكتروني - Legatoo"
            elif language == "bilingual":
                subject = "Verify Your Email - Legatoo | تأكيد البريد الإلكتروني - Legatoo"
            else:
                subject = "Verify Your Email - Legatoo"
            
            message["Subject"] = subject
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
    
    async def send_password_reset_email(self, to_email: str, user_name: str, reset_token: str) -> bool:
        """
        Send password reset email to user.
        
        Args:
            to_email: Recipient email address
            user_name: User's name for personalization
            reset_token: Password reset token
            
        Returns:
            bool: True if email sent successfully, False otherwise
            
        Raises:
            ApiException: If email sending fails
        """
        try:
            if not self.smtp_username or not self.smtp_password:
                logger.warning("SMTP not configured, skipping password reset email")
                return False
            
            # Create reset URL using centralized config
            reset_url = self.url_config.get_password_reset_url(reset_token)
            
            # Create email content
            html_content = self.create_password_reset_email_html(user_name, reset_token, reset_url)
            text_content = self.create_password_reset_email_text(user_name, reset_token, reset_url)
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = f"Password Reset - Legatoo"
            message["From"] = f"{self.from_name} <{self.from_email}>"
            message["To"] = to_email
            
            # Add both HTML and text versions
            text_part = MIMEText(text_content, "plain")
            html_part = MIMEText(html_content, "html")
            
            message.attach(text_part)
            message.attach(html_part)
            
            # Send email using asyncio
            await self._send_email_async(message, to_email)
            
            logger.info(f"Password reset email sent successfully to {to_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send password reset email to {to_email}: {str(e)}")
            raise_error_response(
                status_code=500,
                message="Failed to send password reset email",
                field="email"
            )
    
    def create_password_reset_email_html(self, user_name: str, reset_token: str, reset_url: str) -> str:
        """Create HTML email template for password reset."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Password Reset - Legatoo</title>
            <style>
                * {{
                    margin: 0;
                    padding: 0;
                    box-sizing: border-box;
                }}
                body {{
                    font-family: 'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #1a1a1a;
                    background-color: #f8fafc;
                    padding: 20px;
                }}
                .email-container {{
                    max-width: 600px;
                    margin: 0 auto;
                    background: white;
                    border-radius: 24px;
                    box-shadow: 0 32px 64px rgba(0, 0, 0, 0.12);
                    overflow: hidden;
                }}
                .header {{
                    background:#679594;
                    color: white;
                    padding: 40px 30px;
                    text-align: center;
                    position: relative;
                }}
                .header::before {{
                    content: '';
                    position: absolute;
                    top: 0;
                    left: 0;
                    right: 0;
                    height: 6px;
                    background: #679594;
                }}
                .logo {{
                    width: 180px;
                    height: auto;
                    background: rgba(255, 255, 255, 0.2);
                    border-radius: 20px;
                    margin: 0 auto 20px;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    backdrop-filter: blur(10px);
                    overflow: hidden;
                }}
                .logo img {{
                    width: 100%;
                    height: 100%;
                    object-fit: contain;
                }}
                .brand-name {{
                    font-size: 32px;
                    font-weight: 700;
                    margin-bottom: 8px;
                    letter-spacing: -0.5px;
                }}
                .tagline {{
                    font-size: 16px;
                    opacity: 0.9;
                    font-weight: 400;
                }}
                .content {{
                    padding: 40px 30px;
                }}
                .greeting {{
                    font-size: 18px;
                    font-weight: 600;
                    color: #1a1a1a;
                    margin-bottom: 20px;
                }}
                .message {{
                    font-size: 16px;
                    color: #6b7280;
                    margin-bottom: 30px;
                    line-height: 1.7;
                }}
                .button-container {{
                    text-align: center;
                    margin: 30px 0;
                }}
                .button {{
                    display: inline-block;
                    background: #679594;
                    color: white important;
                    padding: 16px 32px;
                    text-decoration: none;
                    border-radius: 12px;
                    font-weight: 600;
                    font-size: 16px;
                    box-shadow: 0 4px 16px rgba(24, 41, 91, 0.3);
                    transition: all 0.2s ease;
                }}
                .button:hover {{
                    transform: translateY(-1px);
                    box-shadow: 0 8px 24px rgba(24, 41, 91, 0.4);
                }}
                .link-fallback {{
                    background: #f8fafc;
                    border: 1px solid #e2e8f0;
                    border-radius: 12px;
                    padding: 20px;
                    margin: 20px 0;
                    font-size: 14px;
                    color: #6b7280;
                }}
                .link-fallback strong {{
                    color: #374151;
                    display: block;
                    margin-bottom: 8px;
                }}
                .link-text {{
                    word-break: break-all;
               
                    padding: 12px;
                    border-radius: 8px;
                    font-family: monospace;
                    font-size: 13px;
                }}
                .warning {{
                    background: #fef3c7;
                    border: 1px solid #f59e0b;
                    border-radius: 12px;
                    padding: 20px;
                    margin: 20px 0;
                    font-size: 14px;
                    color: #92400e;
                }}
                .warning strong {{
                    color: #78350f;
                    display: block;
                    margin-bottom: 12px;
                }}
                .warning ul {{
                    margin-left: 20px;
                }}
                .warning li {{
                    margin-bottom: 6px;
                }}
                .signature {{
                    margin-top: 30px;
                    font-size: 16px;
                    color: #374151;
                }}
                .footer {{
                    background: #f8fafc;
                    padding: 30px;
                    text-align: center;
                    border-top: 1px solid #e2e8f0;
                }}
                .footer p {{
                    font-size: 12px;
                    color: #9ca3af;
                    margin-bottom: 8px;
                }}
                @media (max-width: 600px) {{
                    .email-container {{
                        margin: 10px;
                        border-radius: 16px;
                    }}
                    .header, .content, .footer {{
                        padding: 30px 20px;
                    }}
                    .brand-name {{
                        font-size: 28px;
                    }}
                }}
            </style>
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <div class="logo">
                        <img src="https://legatoo.fastestfranchise.net/logo.png" alt="Legatoo Logo">
                    </div>
                    <div class="brand-name">Legatoo</div>
                    <div class="tagline">Your Legal Assistant</div>
                </div>
                <div class="content">
                    <div class="greeting">Hello {user_name},</div>
                    
                    <div class="message">
                        We received a request to reset your password for your Legatoo account. If you made this request, click the button below to create a new password.
                    </div>
                    
                    <div class="button-container">
                        <a href="{reset_url}" class="button">Reset Password</a>
                    </div>
                    
                    <div class="link-fallback">
                        <strong>Button not working?</strong>
                        Copy and paste this link into your browser:
                        <div class="link-text">{reset_url}</div>
                    </div>
                    
                    <div class="warning">
                        <strong>Security Notice:</strong>
                        <ul>
                            <li>This password reset link will expire in 1 hour for your security</li>
                            <li>If you didn't request this reset, please ignore this email</li>
                            <li>Your password will remain unchanged until you click the link</li>
                        </ul>
                    </div>
                    
                    <div class="signature">
                        Best regards,<br>
                        The Legatoo Team
                    </div>
                </div>
                <div class="footer">
                    <p>This is an automated message. Please do not reply to this email.</p>
                    <p>&copy; 2024 Legatoo. All rights reserved.</p>
                    <p>Your trusted legal assistant platform</p>
                </div>
            </div>
        </body>
        </html>
        """
    
    def create_password_reset_email_text(self, user_name: str, reset_token: str, reset_url: str) -> str:
        """Create plain text email template for password reset."""
        return f"""
        Password Reset - Legatoo
        
        Hello {user_name},
        
        We received a request to reset your password for your Legatoo account. If you made this request, visit the following link to create a new password:
        
        {reset_url}
        
        Security Notice:
        - This password reset link will expire in 1 hour for your security
        - If you didn't request this reset, please ignore this email
        - Your password will remain unchanged until you click the link
        
        Best regards,
        The Legatoo Team
        
        ---
        This is an automated message. Please do not reply to this email.
        © 2024 Legatoo. All rights reserved.
        Your trusted legal assistant platform
        """
    
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
