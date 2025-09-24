from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, Dict, Any
import httpx
import os
from datetime import datetime, timedelta

from ..db.database import get_db
from ..utils.auth import get_current_user, TokenData
from ..services.profile_service import ProfileService
from ..schemas.profile import ProfileCreate, AccountTypeEnum
from ..services.subscription_service import SubscriptionServiceNew
from ..utils.profile_creation import ensure_user_profile
from pydantic import BaseModel, EmailStr, Field, validator
import re

router = APIRouter(prefix="/supabase-auth", tags=["supabase-authentication"])

# Security scheme
security = HTTPBearer()

# Pydantic models for request/response
class SignupRequest(BaseModel):
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, max_length=128, description="Password must be 8-128 characters")
    first_name: Optional[str] = Field(None, min_length=1, max_length=100, description="First name (1-100 characters)")
    last_name: Optional[str] = Field(None, min_length=1, max_length=100, description="Last name (1-100 characters)")
    phone_number: Optional[str] = Field(None, max_length=20, description="Saudi phone number (must start with 05 and be exactly 10 digits)")
    
    @validator('password')
    def validate_password(cls, v):
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if len(v) > 128:
            raise ValueError('Password must be no more than 128 characters long')
        
        # Check for at least one uppercase letter
        if not re.search(r'[A-Z]', v):
            raise ValueError('Password must contain at least one uppercase letter')
        
        # Check for at least one lowercase letter
        if not re.search(r'[a-z]', v):
            raise ValueError('Password must contain at least one lowercase letter')
        
        # Check for at least one digit
        if not re.search(r'\d', v):
            raise ValueError('Password must contain at least one digit')
        
        # Check for at least one special character
        if not re.search(r'[!@#$%^&*(),.?":{}|<>]', v):
            raise ValueError('Password must contain at least one special character')
        
        return v
    
    @validator('first_name')
    def validate_first_name(cls, v):
        """Validate first name"""
        if v is not None:
            # Remove extra whitespace
            v = v.strip()
            if not v:
                raise ValueError('First name cannot be empty or only whitespace')
            
            # Check for valid characters (letters, spaces, hyphens, apostrophes)
            if not re.match(r"^[a-zA-Z\s\-']+$", v):
                raise ValueError('First name can only contain letters, spaces, hyphens, and apostrophes')
            
            # Check for consecutive special characters
            if re.search(r'[\s\-\']{2,}', v):
                raise ValueError('First name cannot have consecutive spaces, hyphens, or apostrophes')
        
        return v
    
    @validator('last_name')
    def validate_last_name(cls, v):
        """Validate last name"""
        if v is not None:
            # Remove extra whitespace
            v = v.strip()
            if not v:
                raise ValueError('Last name cannot be empty or only whitespace')
            
            # Check for valid characters (letters, spaces, hyphens, apostrophes)
            if not re.match(r"^[a-zA-Z\s\-']+$", v):
                raise ValueError('Last name can only contain letters, spaces, hyphens, and apostrophes')
            
            # Check for consecutive special characters
            if re.search(r'[\s\-\']{2,}', v):
                raise ValueError('Last name cannot have consecutive spaces, hyphens, or apostrophes')
        
        return v
    
    @validator('phone_number')
    def validate_phone_number(cls, v):
        """Validate Saudi phone number format - must start with 05 and be exactly 10 digits"""
        if v is not None:
            # Remove all non-digit characters for validation
            digits_only = re.sub(r'\D', '', v)
            
            # Check if it's exactly 10 digits
            if len(digits_only) != 10:
                raise ValueError('Phone number must be exactly 10 digits')
            
            # Check if it starts with 05 (Saudi mobile number)
            if not digits_only.startswith('05'):
                raise ValueError('Phone number must start with 05 (Saudi mobile number)')
            
            # Check for valid Saudi mobile number pattern (05xxxxxxxx)
            if not re.match(r'^05[0-9]{8}$', digits_only):
                raise ValueError('Invalid Saudi mobile number format')
        
        return v
    
    @validator('email')
    def validate_email_domain(cls, v):
        """Validate email domain"""
        # Check for common disposable email domains
        disposable_domains = [
            '10minutemail.com', 'tempmail.org', 'guerrillamail.com',
            'mailinator.com', 'throwaway.email', 'temp-mail.org'
        ]
        
        domain = v.split('@')[1].lower()
        if domain in disposable_domains:
            raise ValueError('Disposable email addresses are not allowed')
        
        return v

class SigninRequest(BaseModel):
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=1, description="Password cannot be empty")

class SignupResponse(BaseModel):
    message: str
    user: Dict[str, Any]
    profile: Optional[Dict[str, Any]] = None
    profile_created: Optional[bool] = None
    profile_message: Optional[str] = None
    session: Optional[Dict[str, Any]] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[int] = None
    warning: Optional[str] = None
    

class SigninResponse(BaseModel):
    message: str
    user: Dict[str, Any]
    session: Optional[Dict[str, Any]] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    expires_at: Optional[int] = None

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://otiivelflvidgyfshmjn.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# Debug: Print the actual values being used
print(f"🔧 DEBUG: SUPABASE_URL = {SUPABASE_URL}")
print(f"🔧 DEBUG: SUPABASE_ANON_KEY = {SUPABASE_ANON_KEY[:20]}..." if SUPABASE_ANON_KEY else "🔧 DEBUG: SUPABASE_ANON_KEY = None")

if not SUPABASE_ANON_KEY:
    print("⚠️  WARNING: SUPABASE_ANON_KEY not found in environment variables.")
    print("Please add SUPABASE_ANON_KEY to your environment variables.")

@router.post("/signup", response_model=SignupResponse)
async def signup_with_supabase(
    signup_data: SignupRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Sign up a new user with Supabase Auth.
    This will create a real user and return a real JWT token.
    
    Validation Rules:
    - Email: Must be a valid email address, not disposable
    - Password: 8-128 characters, must contain uppercase, lowercase, digit, and special character
    - First Name: 1-100 characters, letters, spaces, hyphens, apostrophes only
    - Last Name: 1-100 characters, letters, spaces, hyphens, apostrophes only
    - Phone Number: Must start with 05 and be exactly 10 digits (Saudi mobile number)
    """
    if not SUPABASE_ANON_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase configuration not found"
        )
    
    # Additional validation for required fields when profile creation is expected
    if not signup_data.first_name and not signup_data.last_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least first name or last name must be provided for profile creation"
        )
    
    # Prepare user metadata
    user_metadata = {}
    if signup_data.first_name:
        user_metadata["first_name"] = signup_data.first_name
    if signup_data.last_name:
        user_metadata["last_name"] = signup_data.last_name
    if signup_data.phone_number:
        user_metadata["phone_number"] = signup_data.phone_number
    
    # Sign up with Supabase
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{SUPABASE_URL}/auth/v1/signup",
                headers={
                    "apikey": SUPABASE_ANON_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "email": signup_data.email,
                    "password": signup_data.password,
                    "data": user_metadata
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Debug: Log the response data
                print(f"Supabase signup response: {data}")
                
                # Supabase returns user data directly, not nested under "user" key
                user_data = data
                
                # Ensure user_data is valid
                if not user_data or not user_data.get("id"):
                    print(f"Invalid user data: {user_data}")
                    raise HTTPException(
                        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                        detail="User creation failed - invalid user data returned"
                    )
                
                # Create profile automatically after successful signup
                try:
                    # Use utility function to ensure profile exists
                    profile_result = await ensure_user_profile(
                        db=db,
                        user_id=user_data["id"],
                        first_name=signup_data.first_name,
                        last_name=signup_data.last_name,
                        phone_number=signup_data.phone_number,
                        avatar_url=None,
                        account_type=AccountTypeEnum.PERSONAL
                    )
                    
                    profile = profile_result["profile"]
                    
                    return {
                        "message": "User created successfully",
                        "user": user_data,
                        "profile": {
                            "id": str(profile.id),
                            "first_name": profile.first_name,
                            "last_name": profile.last_name,
                            "phone_number": profile.phone_number,
                            "account_type": profile.account_type
                        } if profile else None,
                        "profile_created": profile_result["created"],
                        "profile_message": profile_result["message"],
                        "session": None,  # Supabase signup doesn't return session data
                        "access_token": None,  # User needs to sign in separately
                        "refresh_token": None,
                        "expires_at": None
                    }
                    
                except Exception as profile_error:
                    # If profile creation fails, still return user data but log the error
                    print(f"Warning: Failed to create profile for user {user_data['id']}: {str(profile_error)}")
                    return {
                        "message": "User created successfully, but profile creation failed",
                        "user": user_data,
                        "profile": None,
                        "session": None,  # Supabase signup doesn't return session data
                        "access_token": None,  # User needs to sign in separately
                        "refresh_token": None,
                        "expires_at": None,
                        "warning": "Profile creation failed - user can create profile later"
                    }
            else:
                try:
                    error_data = response.json()
                    error_message = error_data.get("msg", error_data.get("message", "Signup failed"))
                except:
                    error_message = f"Signup failed with status {response.status_code}"
                
                raise HTTPException(
                    status_code=response.status_code,
                    detail=error_message
                )
                
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to connect to Supabase: {str(e)}"
            )

@router.post("/signin", response_model=SigninResponse)
async def signin_with_supabase(
    signin_data: SigninRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Sign in with Supabase Auth.
    This will authenticate the user and return a real JWT token.
    """
    if not SUPABASE_ANON_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase configuration not found"
        )
    
    # Sign in with Supabase
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{SUPABASE_URL}/auth/v1/token?grant_type=password",
                headers={
                    "apikey": SUPABASE_ANON_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "email": signin_data.email,
                    "password": signin_data.password
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "message": "Sign in successful",
                    "user": data.get("user"),
                    "session": data.get("session"),
                    "access_token": data.get("access_token"),
                    "refresh_token": data.get("refresh_token"),
                    "expires_at": data.get("expires_at")
                }
            else:
                try:
                    error_data = response.json()
                    error_msg = error_data.get("error_description", error_data.get("msg", "Sign in failed"))
                except:
                    error_msg = f"Sign in failed with status {response.status_code}: {response.text}"
                
                raise HTTPException(
                    status_code=response.status_code,
                    detail={
                        "error": error_msg,
                        "status_code": response.status_code,
                        "response_text": response.text,
                        "supabase_url": SUPABASE_URL
                    }
                )
                
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to connect to Supabase: {str(e)}"
            )


@router.post("/refresh")
async def refresh_token(
    refresh_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh an expired JWT token using the refresh token.
    """
    if not SUPABASE_ANON_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase configuration not found"
        )
    
    # Refresh token with Supabase
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{SUPABASE_URL}/auth/v1/token?grant_type=refresh_token",
                headers={
                    "apikey": SUPABASE_ANON_KEY,
                    "Content-Type": "application/json"
                },
                json={
                    "refresh_token": refresh_token
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "message": "Token refreshed successfully",
                    "access_token": data.get("access_token"),
                    "refresh_token": data.get("refresh_token"),
                    "expires_at": data.get("expires_at")
                }
            else:
                error_data = response.json()
                raise HTTPException(
                    status_code=response.status_code,
                    detail=error_data.get("error_description", "Token refresh failed")
                )
                
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to connect to Supabase: {str(e)}"
            )

@router.post("/signout")
async def signout_with_supabase(
    access_token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Sign out the user and invalidate the JWT token.
    """
    if not SUPABASE_ANON_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase configuration not found"
        )
    
    # Sign out with Supabase
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{SUPABASE_URL}/auth/v1/logout",
                headers={
                    "apikey": SUPABASE_ANON_KEY,
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json"
                }
            )
            
            if response.status_code == 204:
                return {"message": "Sign out successful"}
            else:
                error_data = response.json()
                raise HTTPException(
                    status_code=response.status_code,
                    detail=error_data.get("msg", "Sign out failed")
                )
                
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to connect to Supabase: {str(e)}"
            )

@router.get("/user")
async def get_supabase_user(
    current_user: TokenData = Depends(get_current_user)
):
    """
    Get current user information from the JWT token.
    """
    return {
        "user_id": str(current_user.sub),
        "email": current_user.email,
        "phone": current_user.phone,
        "aud": current_user.aud,
        "role": current_user.role,
        "iat": current_user.iat,
        "exp": current_user.exp,
        "iss": current_user.iss
    }


@router.get("/debug")
async def debug_supabase_config():
    """
    Debug Supabase configuration and test connection.
    """
    config_status = {
        "supabase_url": SUPABASE_URL,
        "supabase_anon_key_set": bool(SUPABASE_ANON_KEY),
        "supabase_anon_key_length": len(SUPABASE_ANON_KEY) if SUPABASE_ANON_KEY else 0,
        "supabase_jwt_secret_set": bool(os.getenv("SUPABASE_JWT_SECRET")),
    }
    
    # Test connection to Supabase
    test_connection = None
    if SUPABASE_ANON_KEY:
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{SUPABASE_URL}/rest/v1/",
                    headers={
                        "apikey": SUPABASE_ANON_KEY,
                        "Authorization": f"Bearer {SUPABASE_ANON_KEY}"
                    }
                )
                test_connection = {
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "error": response.text if response.status_code != 200 else None
                }
        except Exception as e:
            test_connection = {
                "success": False,
                "error": str(e)
            }
    
    return {
        "message": "Supabase Configuration Debug",
        "config": config_status,
        "connection_test": test_connection,
        "next_steps": [
            "1. Check if SUPABASE_ANON_KEY is correctly set",
            "2. Verify Supabase project is active",
            "3. Create user mohammed211920@gmail.com in Supabase Auth",
            "4. Test signin endpoint"
        ]
    }



