from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from fastapi import HTTPException
from supabase import create_client, Client
from ..config.logging_config import get_logger
from ..schemas.response import raise_error_response

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
            # First, check if user already exists in Supabase Auth
            try:
                # Try to get user by email to check if they already exist
                existing_user = self.client.auth.admin.get_user_by_email(email)
                if existing_user and existing_user.user:
                    logger.warning(f"User with email {email} already exists in Supabase Auth")
                    raise_error_response(
                        status_code=422,
                        message="Email already registered",
                        field="email"
                    )
            except Exception as check_error:
                # If we can't check (e.g., user doesn't exist), continue with signup
                logger.debug(f"User existence check for {email}: {str(check_error)}")
                pass
            
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
                raise_error_response(
                    status_code=400,
                    message="User registration failed",
                    field="email"
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
            # Handle Supabase-specific errors using proper exception types and HTTP status codes
            logger.warning(f"Supabase signup error for email {email}: {str(e)}")
            
            # Import Supabase-specific exceptions
            from supabase_auth.errors import AuthApiError
            from httpx import HTTPStatusError
            
            # Check if it's an HTTP status error (from httpx)
            if isinstance(e, HTTPStatusError):
                status_code = e.response.status_code
                logger.info(f"HTTP status error for {email}: {status_code}")
                
                if status_code == 400:
                    # 400 Bad Request - usually invalid email format or validation error
                    raise_error_response(
                        status_code=400,
                        message="Invalid email format",
                        field="email"
                    )
                elif status_code == 409:
                    # 409 Conflict - usually duplicate email
                    raise_error_response(
                        status_code=422,
                        message="Email already registered",
                        field="email"
                    )
                elif status_code == 429:
                    # 429 Too Many Requests - rate limiting
                    raise_error_response(
                        status_code=429,
                        message="Too many requests. Please try again later.",
                        field="email"
                    )
                else:
                    # Other HTTP errors
                    raise_error_response(
                        status_code=500,
                        message="Authentication service unavailable",
                        field="email"
                    )
            
            # Check if it's a Supabase Auth API error
            elif isinstance(e, AuthApiError):
                logger.info(f"Supabase Auth API error for {email}: {str(e)}")
                
                # For AuthApiError, we can check the error message more reliably
                error_message = str(e).lower()
                
                # Check for specific known error patterns
                if "already registered" in error_message or "already exists" in error_message:
                    raise_error_response(
                        status_code=422,
                        message="Email already registered",
                        field="email"
                    )
                elif "invalid" in error_message and "email" in error_message:
                    raise_error_response(
                        status_code=400,
                        message="Invalid email format",
                        field="email"
                    )
                else:
                    # Generic Auth API error
                    raise_error_response(
                        status_code=500,
                        message="Authentication service unavailable",
                        field="email"
                    )
            
            else:
                # Log the error with full stack trace and raise a generic exception
                logger.exception(f"Unhandled Supabase signup error for email {email}: {str(e)}")
                raise_error_response(
                    status_code=500,
                    message="Authentication service unavailable",
                    field="email"
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
                raise_error_response(
                    status_code=401,
                    message="Invalid email or password",
                    field="email"
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
            # Handle Supabase-specific errors using proper exception types and HTTP status codes
            logger.warning(f"Supabase login error for email {email}: {str(e)}")
            
            # Import Supabase-specific exceptions
            from supabase_auth.errors import AuthApiError
            from httpx import HTTPStatusError
            
            # Check if it's an HTTP status error (from httpx)
            if isinstance(e, HTTPStatusError):
                status_code = e.response.status_code
                logger.info(f"HTTP status error for login {email}: {status_code}")
                
                if status_code == 401:
                    # 401 Unauthorized - invalid credentials
                    raise_error_response(
                        status_code=401,
                        message="Invalid email or password",
                        field="email"
                    )
                elif status_code == 429:
                    # 429 Too Many Requests - rate limiting
                    raise_error_response(
                        status_code=429,
                        message="Too many requests. Please try again later.",
                        field="email"
                    )
                else:
                    # Other HTTP errors
                    raise_error_response(
                        status_code=500,
                        message="Authentication service unavailable",
                        field="email"
                    )
            
            # Check if it's a Supabase Auth API error
            elif isinstance(e, AuthApiError):
                logger.info(f"Supabase Auth API error for login {email}: {str(e)}")
                
                # For AuthApiError, we can check the error message more reliably
                error_message = str(e).lower()
                
                # Check for specific known error patterns
                if ("invalid" in error_message and ("email" in error_message or "password" in error_message or "credentials" in error_message)):
                    raise_error_response(
                        status_code=401,
                        message="Invalid email or password",
                        field="email"
                    )
                else:
                    # Generic Auth API error
                    raise_error_response(
                        status_code=500,
                        message="Authentication service unavailable",
                        field="email"
                    )
            
            else:
                # Log the error with full stack trace and raise a generic exception
                logger.exception(f"Unhandled Supabase login error for email {email}: {str(e)}")
                raise_error_response(
                    status_code=500,
                    message="Authentication service unavailable",
                    field="email"
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
