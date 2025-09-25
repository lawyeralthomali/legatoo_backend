from fastapi import APIRouter, HTTPException, status, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi.security import HTTPBearer
from typing import Optional, Dict, Any
import httpx
import os
import re

from pydantic import BaseModel, Field, field_validator

# Project imports
from ..db.database import get_db
from ..utils.auth import get_current_user, TokenData
from ..schemas.profile import AccountTypeEnum
from ..utils.profile_creation import ensure_user_profile
from pydantic import EmailStr

# ====================================
# Router & Config
# ====================================
router = APIRouter(prefix="/supabase-auth", tags=["supabase-authentication"])
security = HTTPBearer()

SUPABASE_URL = os.getenv("SUPABASE_URL", "https://otiivelflvidgyfshmjn.supabase.co")
SUPABASE_ANON_KEY = os.getenv("SUPABASE_ANON_KEY")


# ====================================
# Schemas
# ====================================
class SignupRequest(BaseModel):
    email: EmailStr = Field(..., description="Valid email address")
    password: str = Field(..., min_length=8, max_length=128)
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone_number: Optional[str] = Field(None, max_length=20, description="Must be Saudi (05xxxxxxxx)")

    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Ensure strong password policy"""
        if not re.search(r'[A-Z]', v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not re.search(r'[a-z]', v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not re.search(r'\d', v):
            raise ValueError("Password must contain at least one digit")
        if not re.search(r'[!@#$%^&*(),.?\":{}|<>]', v):
            raise ValueError("Password must contain at least one special character")
        return v

    @field_validator('first_name', 'last_name')
    @classmethod
    def validate_names(cls, v: Optional[str]) -> Optional[str]:
        """Validate names format"""
        if v:
            v = v.strip()
            if not re.match(r"^[a-zA-Z\s\-']+$", v):
                raise ValueError("Name can only contain letters, spaces, hyphens, and apostrophes")
            if re.search(r'[\s\-\']{2,}', v):
                raise ValueError("Name cannot contain consecutive special characters")
        return v

    @field_validator('phone_number')
    @classmethod
    def validate_phone_number(cls, v: Optional[str]) -> Optional[str]:
        """Ensure Saudi phone number format"""
        if v:
            digits = re.sub(r'\D', '', v)
            if len(digits) != 10 or not digits.startswith("05"):
                raise ValueError("Phone number must be Saudi format: 05xxxxxxxx")
        return v


class SigninRequest(BaseModel):
    email: str = Field(..., description="Valid email address")
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


# ====================================
# Helpers
# ====================================
async def supabase_request(method: str, endpoint: str, payload: dict = None, headers: dict = None):
    """Reusable helper for Supabase HTTP requests"""
    if not SUPABASE_ANON_KEY:
        raise HTTPException(status_code=500, detail="Supabase configuration not found")

    default_headers = {
        "apikey": SUPABASE_ANON_KEY,
        "Content-Type": "application/json"
    }
    if headers:
        default_headers.update(headers)

    async with httpx.AsyncClient() as client:
        response = await client.request(method, f"{SUPABASE_URL}{endpoint}", headers=default_headers, json=payload)

        if response.status_code >= 400:
            try:
                error = response.json()
            except Exception:
                error = {"message": response.text}
            raise HTTPException(status_code=response.status_code, detail=error)

        return response.json() if response.content else None


# ====================================
# Routes
# ====================================
@router.post("/signup", response_model=SignupResponse)
async def signup_with_supabase(signup_data: SignupRequest, db: AsyncSession = Depends(get_db)):
    """Sign up user in Supabase & create local profile"""
    # 1. Register user in Supabase
    user_data = await supabase_request(
        "POST",
        "/auth/v1/signup",
        payload={
            "email": signup_data.email,
            "password": signup_data.password,
            "data": {
                "first_name": signup_data.first_name,
                "last_name": signup_data.last_name,
                "phone_number": signup_data.phone_number
            }
        }
    )

    user_id = user_data.get("id")
    if not user_id:
        raise HTTPException(status_code=500, detail="Supabase signup succeeded but no user ID returned")

    # 2. Create local profile
    try:
        profile_result = await ensure_user_profile(
            db=db,
            user_id=user_id,
            first_name=signup_data.first_name,
            last_name=signup_data.last_name,
            phone_number=signup_data.phone_number,
            avatar_url=None,
            account_type=AccountTypeEnum.PERSONAL
        )
        profile = profile_result["profile"]

        return SignupResponse(
            message="User and profile created successfully",
            user=user_data,
            profile={
                "id": str(profile.id),
                "first_name": profile.first_name,
                "last_name": profile.last_name,
                "phone_number": profile.phone_number,
                "account_type": profile.account_type
            } if profile else None,
            profile_created=profile_result["created"],
            profile_message=profile_result["message"]
        )
    except Exception as e:
        return SignupResponse(
            message="User created but profile failed",
            user=user_data,
            profile_created=False,
            profile_message=f"Profile creation failed: {str(e)}",
            warning="Profile can be created later"
        )


@router.post("/signin", response_model=SigninResponse)
async def signin_with_supabase(signin_data: SigninRequest):
    """Sign in user with Supabase"""
    data = await supabase_request(
        "POST",
        "/auth/v1/token?grant_type=password",
        payload={"email": signin_data.email, "password": signin_data.password}
    )

    return SigninResponse(
        message="Sign in successful",
        user=data.get("user"),
        session=data.get("session"),
        access_token=data.get("access_token"),
        refresh_token=data.get("refresh_token"),
        expires_at=data.get("expires_at")
    )


@router.post("/refresh")
async def refresh_token(refresh_token: str):
    """Refresh access token"""
    data = await supabase_request(
        "POST",
        "/auth/v1/token?grant_type=refresh_token",
        payload={"refresh_token": refresh_token}
    )
    return {
        "message": "Token refreshed successfully",
        "access_token": data.get("access_token"),
        "refresh_token": data.get("refresh_token"),
        "expires_at": data.get("expires_at"),
    }


@router.post("/signout")
async def signout_with_supabase(access_token: str):
    """Sign out user and invalidate JWT"""
    await supabase_request(
        "POST",
        "/auth/v1/logout",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    return {"message": "Sign out successful"}


@router.get("/user")
async def get_supabase_user(current_user: TokenData = Depends(get_current_user)):
    """Get current authenticated user"""
    return current_user.dict()

