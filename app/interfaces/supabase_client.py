from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
import httpx
import logging
from fastapi import HTTPException

logger = logging.getLogger(__name__)


class ISupabaseClient(ABC):
    """Interface for Supabase authentication operations."""
    
    @abstractmethod
    async def signup(self, email: str, password: str, data: Dict[str, Any]) -> Dict[str, Any]:
      
        pass


class SupabaseClient(ISupabaseClient):
    """Concrete implementation of Supabase client using httpx."""
    
    def __init__(self, supabase_url: str, supabase_anon_key: str):
       
        self.supabase_url = supabase_url
        self.supabase_key = supabase_anon_key
    
    async def signup(self, email: str, password: str, data: Dict[str, Any]) -> Dict[str, Any]:
        import logging
        logger = logging.getLogger(__name__)
       
        headers = {
            "apikey": self.supabase_key,
            "Content-Type": "application/json"
        }
        
        payload = {
            "email": email,
            "password": password,
            "data": data
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.supabase_url}/auth/v1/signup",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code >= 400:
                    # Parse error response - handle both string and dict formats
                    try:
                        error_detail = response.json()
                    except Exception:
                        error_detail = response.text
                    
                    # Log the actual error for debugging
                    logger.error(f"Supabase error - Status: {response.status_code}, Detail: {error_detail}")
                    logger.error(f"Full response: {response.text}")
                    
                    # Map Supabase errors to structured exceptions
                    if response.status_code == 400:
                        if isinstance(error_detail, dict) and error_detail.get("error_code") == "email_address_invalid":
                            raise HTTPException(
                                status_code=400,
                                detail="Invalid email format"
                            )
                        else:
                            raise HTTPException(
                                status_code=400,
                                detail="Invalid email format"
                            )
                    elif response.status_code == 422:
                        # Check for "already registered" in various formats
                        error_text = str(error_detail).lower()
                        if ("already registered" in error_text or 
                            "user already registered" in error_text or
                            "email already exists" in error_text or
                            "user already exists" in error_text or
                            "duplicate" in error_text):
                            raise HTTPException(
                                status_code=422,
                                detail="Email already registered"
                            )
                        else:
                            raise HTTPException(
                                status_code=422,
                                detail="User registration failed"
                            )
                    else:
                        # Check for duplicate user errors in other status codes
                        error_text = str(error_detail).lower()
                        if ("already registered" in error_text or 
                            "user already registered" in error_text or
                            "email already exists" in error_text or
                            "user already exists" in error_text or
                            "duplicate" in error_text or
                            "email address already in use" in error_text or
                            "user with this email already exists" in error_text):
                            raise HTTPException(
                                status_code=422,
                                detail="Email already registered"
                            )
                        else:
                            raise HTTPException(
                                status_code=response.status_code,
                                detail=f"Authentication service error: {error_detail}"
                            )
                
                # Return successful response
                result = response.json() if response.content else {}
                logger.info(f"Supabase signup successful - User ID: {result.get('id', 'No ID')}, Email: {result.get('email', 'No email')}")
                return result
                
        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise
        except Exception as e:
            # Log internal errors and raise generic exception
            logger.error(f"Supabase client error: {str(e)}")
            raise HTTPException(
                status_code=500,
                detail="Authentication service unavailable"
            )
    
    async def check_user_exists(self, email: str) -> bool:
       
        headers = {
            "apikey": self.supabase_key,
            "Authorization": f"Bearer {self.supabase_key}",
            "Content-Type": "application/json"
        }
        
        try:
            async with httpx.AsyncClient() as client:
                # Use Supabase's admin API to check if user exists
                response = await client.get(
                    f"{self.supabase_url}/auth/v1/admin/users",
                    headers=headers,
                    params={"email": email}
                )
                
                if response.status_code == 200:
                    users = response.json()
                    return len(users.get("users", [])) > 0
                else:
                    # If we can't check, assume user doesn't exist to allow signup
                    return False
                    
        except Exception as e:
            logger.warning(f"Could not check if user exists: {str(e)}")
            # If we can't check, assume user doesn't exist to allow signup
            return False
