from jose import JWTError, jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional, Dict, Any
import os
from datetime import datetime
from uuid import UUID
from dotenv import load_dotenv

from ..schemas.profile import TokenData

# Load environment variables
load_dotenv("supabase.env")

# JWT Configuration
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")
SUPABASE_URL = os.getenv("SUPABASE_URL", "https://otiivelflvidgyfshmjn.supabase.co")

# Test JWT Configuration (for testing purposes)
TEST_JWT_SECRET = os.getenv("JWT_SECRET", "your-secret-key-change-in-production")

# Security scheme
security = HTTPBearer()

# If SUPABASE_JWT_SECRET is not set, we'll use the project's JWT secret
# You can get this from Supabase Dashboard > Settings > API > JWT Secret
if not SUPABASE_JWT_SECRET:
    print("⚠️  WARNING: SUPABASE_JWT_SECRET not found in environment variables.")
    print("Please add SUPABASE_JWT_SECRET to your supabase.env file.")
    print("You can find it in Supabase Dashboard > Settings > API > JWT Secret")


def verify_test_token(token: str) -> Optional[TokenData]:
    """
    Verify and decode a test JWT token.
    
    Args:
        token: The JWT token string
        
    Returns:
        TokenData: Decoded token payload or None if invalid
    """
    try:
        # Decode the JWT token
        payload = jwt.decode(
            token,
            TEST_JWT_SECRET,
            algorithms=["HS256"]
        )
        
        # Extract user ID from 'sub' claim
        user_id = payload.get("sub")
        if not user_id:
            return None
        
        # Create TokenData object
        token_data = TokenData(
            sub=UUID(user_id),  # Convert string to UUID
            email=payload.get("email"),
            phone=payload.get("phone"),
            aud=payload.get("aud", "authenticated"),
            role=payload.get("role", "authenticated"),
            iat=payload.get("iat", 0),
            exp=payload.get("exp", 0),
            iss=payload.get("iss", "test"),
            jti=payload.get("jti")
        )
        
        return token_data
        
    except (JWTError, ValueError):
        return None


def verify_supabase_token(token: str) -> TokenData:
    """
    Verify and decode a Supabase JWT token.
    
    Args:
        token: The JWT token string
        
    Returns:
        TokenData: Decoded token payload
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    if not SUPABASE_JWT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="JWT secret not configured"
        )
    
    try:
        # Decode the JWT token
        # Supabase JWT tokens have issuer as {SUPABASE_URL}/auth/v1
        supabase_issuer = f"{SUPABASE_URL}/auth/v1"
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience="authenticated",
            issuer=supabase_issuer
        )
        
        # Extract user ID from 'sub' claim
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token: missing user ID"
            )
        
        # Create TokenData object
        token_data = TokenData(
            sub=UUID(user_id),
            email=payload.get("email"),
            phone=payload.get("phone"),
            aud=payload.get("aud", "authenticated"),
            role=payload.get("role", "authenticated"),
            iat=payload.get("iat", 0),
            exp=payload.get("exp", 0),
            iss=payload.get("iss", SUPABASE_URL),
            jti=payload.get("jti")
        )
        
        return token_data
        
    except JWTError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Could not validate credentials: {str(e)}"
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Invalid user ID format: {str(e)}"
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> TokenData:
    """
    Dependency to get the current authenticated user from JWT token.
    Supports both Supabase JWT and test JWT tokens.
    
    Args:
        credentials: HTTP Bearer token from Authorization header
        
    Returns:
        TokenData: Current user's token data
        
    Raises:
        HTTPException: If token is invalid or user is not authenticated
    """
    token = credentials.credentials
    
    # First try to verify as test token
    test_user = verify_test_token(token)
    if test_user:
        return test_user
    
    # If not a test token, try Supabase token
    try:
        return verify_supabase_token(token)
    except HTTPException:
        # If both fail, raise authentication error
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


async def get_current_user_id(
    current_user: TokenData = Depends(get_current_user)
) -> UUID:
    """
    Dependency to get the current user's ID.
    
    Args:
        current_user: Current user's token data
        
    Returns:
        UUID: Current user's ID
    """
    return current_user.sub
