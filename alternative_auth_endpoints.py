# Alternative: If you want login/register endpoints in FastAPI
# (Not recommended with Supabase Auth, but here's how you'd do it)

from fastapi import APIRouter, Depends, HTTPException, status
from supabase import create_client, Client
import os
from dotenv import load_dotenv

load_dotenv("supabase.env")

# Initialize Supabase client
supabase: Client = create_client(
    os.getenv("SUPABASE_URL"),
    os.getenv("SUPABASE_ANON_KEY")
)

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register")
async def register_user(email: str, password: str):
    """Register a new user via Supabase Auth."""
    try:
        response = supabase.auth.sign_up({
            "email": email,
            "password": password
        })
        
        if response.user:
            return {
                "message": "User registered successfully",
                "user_id": response.user.id,
                "email": response.user.email
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Registration failed"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Registration error: {str(e)}"
        )

@router.post("/login")
async def login_user(email: str, password: str):
    """Login user via Supabase Auth."""
    try:
        response = supabase.auth.sign_in_with_password({
            "email": email,
            "password": password
        })
        
        if response.session:
            return {
                "message": "Login successful",
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "user_id": response.user.id
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Login error: {str(e)}"
        )

@router.post("/reset-password")
async def reset_password(email: str):
    """Send password reset email via Supabase Auth."""
    try:
        response = supabase.auth.reset_password_email(email)
        return {
            "message": "Password reset email sent",
            "email": email
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password reset error: {str(e)}"
        )

@router.post("/logout")
async def logout_user(token: str):
    """Logout user via Supabase Auth."""
    try:
        supabase.auth.sign_out()
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Logout error: {str(e)}"
        )

