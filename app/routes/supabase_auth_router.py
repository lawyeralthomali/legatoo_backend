from fastapi import APIRouter, HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional
import httpx
import os
from datetime import datetime, timedelta

from ..db.database import get_db
from ..utils.auth import get_current_user, TokenData
from ..services.subscription_service_new import SubscriptionServiceNew

router = APIRouter(prefix="/supabase-auth", tags=["supabase-authentication"])

# Security scheme
security = HTTPBearer()

# Supabase configuration
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://otiivelflvidgyfshmjn.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")

# Debug: Print the actual values being used
print(f"🔧 DEBUG: SUPABASE_URL = {SUPABASE_URL}")
print(f"🔧 DEBUG: SUPABASE_ANON_KEY = {SUPABASE_ANON_KEY[:20]}..." if SUPABASE_ANON_KEY else "🔧 DEBUG: SUPABASE_ANON_KEY = None")

if not SUPABASE_ANON_KEY:
    print("⚠️  WARNING: SUPABASE_ANON_KEY not found in environment variables.")
    print("Please add SUPABASE_ANON_KEY to your environment variables.")

@router.post("/signup")
async def signup_with_supabase(
    email: str,
    password: str,
    full_name: str = None,
    db: AsyncSession = Depends(get_db)
):
    """
    Sign up a new user with Supabase Auth.
    This will create a real user and return a real JWT token.
    """
    if not SUPABASE_ANON_KEY:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Supabase configuration not found"
        )
    
    # Prepare user metadata
    user_metadata = {}
    if full_name:
        user_metadata["full_name"] = full_name
    
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
                    "email": email,
                    "password": password,
                    "data": user_metadata
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "message": "User created successfully",
                    "user": data.get("user"),
                    "session": data.get("session"),
                    "access_token": data.get("session", {}).get("access_token"),
                    "refresh_token": data.get("session", {}).get("refresh_token"),
                    "expires_at": data.get("session", {}).get("expires_at")
                }
            else:
                error_data = response.json()
                raise HTTPException(
                    status_code=response.status_code,
                    detail=error_data.get("msg", "Signup failed")
                )
                
        except httpx.RequestError as e:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to connect to Supabase: {str(e)}"
            )

@router.post("/signin")
async def signin_with_supabase(
    email: str,
    password: str,
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
                    "email": email,
                    "password": password
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



