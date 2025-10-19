# SOLID Signup Implementation - Complete Guide

## Overview

This document provides a complete SOLID-compliant implementation of the FastAPI signup flow with proper separation of concerns, dependency injection, and unified response handling.

## 🏗️ Architecture Components

### 1. Unified Response Helper (`app/schemas/unified_responses.py`)

```python
def unified_response(
    success: bool, 
    message: str, 
    data: Optional[Any] = None, 
    errors: Optional[List[ErrorDetail]] = None
) -> JSONResponse
```

**Features:**
- ✅ Consistent JSON structure across all endpoints
- ✅ Type-safe with Pydantic models
- ✅ Follows .cursorrules guidelines exactly

### 2. Supabase Client Interface (`app/interfaces/supabase_client.py`)

**Interface:**
```python
class ISupabaseClient(ABC):
    @abstractmethod
    async def signup(self, email: str, password: str, data: Dict[str, Any]) -> Dict[str, Any]:
        pass
```

**Implementation:**
- ✅ Robust error mapping from Supabase responses
- ✅ Handles both string and dict error formats
- ✅ Structured exception handling
- ✅ Logging for internal errors

### 3. Profile Repository (`app/interfaces/profile_repository.py`)

**Interface:**
```python
class IProfileRepository(ABC):
    @abstractmethod
    async def email_exists(self, email: str) -> bool: pass
    @abstractmethod
    async def get_profile_by_id(self, user_id: UUID) -> Optional[Profile]: pass
    @abstractmethod
    async def create_profile(self, user_id: UUID, profile_data: ProfileCreate) -> Profile: pass
```

**Implementation:**
- ✅ Database operations with AsyncSession
- ✅ Race condition handling with IntegrityError
- ✅ Transaction management
- ✅ Proper error logging

### 4. Profile Service (`app/services/profile_service.py`)

**Business Logic:**
- ✅ Email uniqueness validation
- ✅ Default value application (first_name, last_name, account_type)
- ✅ Business rule enforcement
- ✅ Service orchestration

### 5. Authentication Router (`app/routes/auth_router.py`)

**Features:**
- ✅ Thin route handlers
- ✅ Dependency injection for all services
- ✅ Database transaction management
- ✅ Comprehensive error handling
- ✅ Unified response format

## 🔧 Dependency Injection Setup

### Production Wiring Example

```python
# In your main FastAPI app (app/main.py)
from app.routes.auth_router import router as auth_router
from app.interfaces.supabase_client import ISupabaseClient, SupabaseClient
from app.interfaces.profile_repository import IProfileRepository, ProfileRepository
from app.services.profile_service import ProfileService

app = FastAPI()

# Register routers
app.include_router(auth_router, prefix="/api/v1")

# Dependency overrides for production
def get_production_supabase_client() -> ISupabaseClient:
    return SupabaseClient(
        supabase_url=os.getenv("SUPABASE_URL"),
        supabase_anon_key=os.getenv("SUPABASE_ANON_KEY")
    )

# Override dependencies if needed
app.dependency_overrides[get_supabase_client] = get_production_supabase_client
```

### Testing Setup Example

```python
# In your test files
from unittest.mock import AsyncMock, MagicMock
from app.interfaces.supabase_client import ISupabaseClient
from app.interfaces.profile_repository import IProfileRepository

# Mock implementations for testing
class MockSupabaseClient(ISupabaseClient):
    async def signup(self, email: str, password: str, data: dict) -> dict:
        return {"id": "test-uuid", "email": email}

class MockProfileRepository(IProfileRepository):
    async def email_exists(self, email: str) -> bool:
        return False  # Email is unique
    
    async def create_profile(self, user_id: UUID, profile_data: ProfileCreate) -> Profile:
        return Profile(id=user_id, first_name="Test", last_name="User")

# Override dependencies in tests
app.dependency_overrides[get_supabase_client] = lambda: MockSupabaseClient()
app.dependency_overrides[get_profile_repository] = lambda: MockProfileRepository()
```

## 🚀 Extension Guidelines

### 1. Making Unified Response Default Across App

**Step 1: Update all existing routers**
```python
# In each router file
from app.schemas.unified_responses import unified_response, ErrorDetail

# Replace all return statements with unified_response()
return unified_response(success=True, message="Success", data=result)
```

**Step 2: Create response model base classes**
```python
# In app/schemas/unified_responses.py
class BaseResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Any] = None
    errors: List[ErrorDetail] = Field(default_factory=list)

# Use in all endpoint response models
class UserResponse(BaseResponse):
    pass
```

**Step 3: Add global exception handler**
```python
# In app/main.py
from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global exception: {str(exc)}")
    return unified_response(
        success=False,
        message="Internal server error",
        data=None,
        errors=[ErrorDetail(field=None, message="An unexpected error occurred")]
    )
```

### 2. Configuring Supabase Rollback Policy

**Option 1: Keep Supabase User (Recommended)**
```python
# In app/services/profile_service.py
class ProfileService:
    def __init__(self, profile_repository: IProfileRepository, config: dict):
        self.profile_repository = profile_repository
        self.keep_supabase_user_on_failure = config.get("keep_supabase_user", True)
    
    async def create_profile_for_user(self, user_id: UUID, ...):
        try:
            profile = await self.profile_repository.create_profile(user_id, profile_data)
            return ProfileResponse.from_orm(profile)
        except IntegrityError:
            if self.keep_supabase_user_on_failure:
                logger.warning(f"Keeping Supabase user {user_id} despite profile creation failure")
                raise
            else:
                # Optionally delete Supabase user
                await self._cleanup_supabase_user(user_id)
                raise
```

**Option 2: Environment Configuration**
```python
# In app/config/settings.py
class Settings(BaseSettings):
    keep_supabase_user_on_profile_failure: bool = True
    supabase_cleanup_on_failure: bool = False
    
    class Config:
        env_file = ".env"
```

**Option 3: Admin Interface for Cleanup**
```python
# In app/routes/admin_router.py
@router.post("/cleanup/orphaned-users")
async def cleanup_orphaned_users():
    """Clean up Supabase users without local profiles"""
    # Implementation to find and clean up orphaned users
    pass
```

## 📊 Response Examples

### Successful Signup Response
```json
{
  "success": true,
  "message": "User and profile created successfully",
  "data": {
    "user": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "email": "user@example.com",
      "created_at": "2024-01-01T00:00:00Z",
      "aud": "authenticated",
      "role": "authenticated"
    },
    "profile": {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "first_name": "John",
      "last_name": "Doe",
      "phone_number": "0509556183",
      "account_type": "personal",
      "created_at": "2024-01-01T00:00:00Z"
    }
  },
  "errors": []
}
```

### Email Already Registered Error Response
```json
{
  "success": false,
  "message": "Email already registered",
  "data": null,
  "errors": [
    {
      "field": "email",
      "message": "This email is already in use."
    }
  ]
}
```

### Invalid Email Format Error Response
```json
{
  "success": false,
  "message": "Invalid email format",
  "data": null,
  "errors": [
    {
      "field": "email",
      "message": "The provided email is invalid."
    }
  ]
}
```

### Profile Creation Failed Error Response
```json
{
  "success": false,
  "message": "Profile creation failed",
  "data": null,
  "errors": [
    {
      "field": "profile",
      "message": "Failed to create user profile"
    }
  ]
}
```

### Auth Service Error Response
```json
{
  "success": false,
  "message": "User creation failed",
  "data": null,
  "errors": [
    {
      "field": null,
      "message": "Auth service error: Authentication service unavailable"
    }
  ]
}
```

## 🎯 SOLID Principles Applied

### Single Responsibility Principle (SRP)
- ✅ **Router**: Only handles HTTP request/response
- ✅ **Service**: Only contains business logic
- ✅ **Repository**: Only handles data access
- ✅ **Client**: Only handles external API communication

### Open/Closed Principle (OCP)
- ✅ **Interfaces**: Allow extension without modification
- ✅ **Dependency Injection**: Easy to swap implementations
- ✅ **Configuration**: Behavior changes through config, not code

### Liskov Substitution Principle (LSP)
- ✅ **Interface Implementations**: Can be substituted seamlessly
- ✅ **Mock Objects**: Test implementations follow same contracts
- ✅ **Polymorphism**: All implementations work identically

### Interface Segregation Principle (ISP)
- ✅ **Focused Interfaces**: Each interface has single purpose
- ✅ **No Fat Interfaces**: Clients only depend on what they use
- ✅ **Clean Contracts**: Clear, minimal interface definitions

### Dependency Inversion Principle (DIP)
- ✅ **Abstractions**: High-level modules depend on abstractions
- ✅ **Dependency Injection**: Dependencies injected, not created
- ✅ **Inversion of Control**: Framework controls object creation

## 🧪 Testing Strategy

### Unit Tests
- Test each component in isolation
- Mock dependencies using interfaces
- Verify business logic correctness

### Integration Tests
- Test component interactions
- Use test database
- Verify end-to-end flows

### Contract Tests
- Verify interface implementations
- Test error handling
- Validate response formats

This implementation provides a solid foundation for scalable, maintainable, and testable FastAPI applications following SOLID principles! 🚀
