from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from fastapi import HTTPException
from supabase import create_client, Client
from ..config.logging_config import get_logger

logger = get_logger(__name__)


class ISupabaseClient(ABC):
    """Interface for Supabase authentication operations."""
    
    @abstractmethod
    def signup(self, email: str, password: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Sign up a new user with Supabase Auth."""
        pass
    
    @abstractmethod
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """Login a user with Supabase Auth."""
        pass
    
    @abstractmethod
    def check_user_exists(self, email: str) -> bool:
        """Check if a user exists in the profiles table."""
        pass


class SupabaseClient(ISupabaseClient):
    """Concrete implementation of Supabase client using official supabase-py library."""
    
    def __init__(self, supabase_url: str, supabase_anon_key: str):
        """Initialize Supabase client with URL and anon key."""
        self.supabase_url = supabase_url
        self.supabase_key = supabase_anon_key
        self._client: Optional[Client] = None
    
    @property
    def client(self) -> Client:
        """Get or create Supabase client instance."""
        if self._client is None:
            self._client = create_client(self.supabase_url, self.supabase_key)
        return self._client
    
    def signup(self, email: str, password: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Sign up a new user using Supabase Auth.
        
        Args:
            email: User's email address
            password: User's password
            data: Additional user metadata
            
        Returns:
            Dict containing user information
            
        Raises:
            HTTPException: For various error conditions
        """
        try:
            # Use the official Supabase client for signup
            response = self.client.auth.sign_up({
                "email": email,
                "password": password,
                "options": {
                    "data": data
                }
            })
            
            # Check if signup was successful
            if response.user is None:
                raise HTTPException(
                    status_code=400,
                    detail="User registration failed"
                )
            
            # Log successful signup
            logger.info(f"Supabase signup successful - User ID: {response.user.id}, Email: {response.user.email}")
            
            # Return user data in the expected format
            return {
                "id": response.user.id,
                "email": response.user.email,
                "created_at": response.user.created_at,
                "user_metadata": response.user.user_metadata
            }
            
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            # Handle Supabase-specific errors
            error_str = str(e).lower()
            
            # Check for duplicate email errors
            if ("already registered" in error_str or 
                "user already registered" in error_str or
                "email already exists" in error_str or
                "user already exists" in error_str or
                "duplicate" in error_str or
                "email address already in use" in error_str or
                "user with this email already exists" in error_str):
                raise HTTPException(
                    status_code=422,
                    detail="Email already registered"
                )
            # Check for invalid email format
            elif ("invalid email" in error_str or 
                  "email_address_invalid" in error_str):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid email format"
                )
            else:
                # Log the error with full stack trace and raise a generic exception
                logger.exception(f"Supabase signup error for email {email}")
                raise HTTPException(
                    status_code=500,
                    detail="Authentication service unavailable"
                )
    
    def login(self, email: str, password: str) -> Dict[str, Any]:
        """
        Login a user using Supabase Auth.
        
        Args:
            email: User's email address
            password: User's password
            
        Returns:
            Dict containing user and session information
            
        Raises:
            HTTPException: For various error conditions
        """
        try:
            # Use the official Supabase client for login
            response = self.client.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            
            # Check if login was successful
            if response.user is None or response.session is None:
                raise HTTPException(
                    status_code=401,
                    detail="Invalid email or password"
                )
            
            # Log successful login
            logger.info(f"Supabase login successful - User ID: {response.user.id}, Email: {response.user.email}")
            
            # Return session data in the expected format
            return {
                "user": {
                    "id": response.user.id,
                    "email": response.user.email,
                    "created_at": response.user.created_at,
                    "user_metadata": response.user.user_metadata
                },
                "access_token": response.session.access_token,
                "refresh_token": response.session.refresh_token,
                "expires_at": response.session.expires_at
            }
            
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            # Handle Supabase-specific errors
            error_str = str(e).lower()
            
            # Check for invalid credentials
            if ("invalid" in error_str and ("email" in error_str or "password" in error_str or "credentials" in error_str)):
                raise HTTPException(
                    status_code=401,
                    detail="Invalid email or password"
                )
            else:
                # Log the error with full stack trace and raise a generic exception
                logger.exception(f"Supabase login error for email {email}")
                raise HTTPException(
                    status_code=500,
                    detail="Authentication service unavailable"
                )
    
    def check_user_exists(self, email: str) -> bool:
        """
        Check if a user exists in the profiles table.
        
        Args:
            email: Email address to check
            
        Returns:
            True if user exists, False otherwise
        """
        try:
            # Query the profiles table to check if user exists
            response = (
                self.client.from_("profiles")
                .select("id")
                .eq("email", email)
                .limit(1)
                .execute()
            )
            user_exists = len(response.data) > 0
            logger.info(f"User existence check for email {email}: {user_exists}")
            return user_exists
                    
        except Exception as e:
            # Log warning and return False to allow signup attempts
            logger.warning(f"Could not check if user exists for email {email}: {str(e)}")
            return False
