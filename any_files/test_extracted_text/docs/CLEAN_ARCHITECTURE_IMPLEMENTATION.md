# Clean Architecture Implementation - Complete Guide

## Overview

This document provides a complete implementation of clean architecture principles for the FastAPI + SQLAlchemy + Pydantic project, following SOLID principles and separation of concerns.

## 🏗️ Architecture Layers

### 1. **Schemas Layer** (`app/schemas/`)
- **`response.py`**: Unified API response models and helper functions
- **`request.py`**: Request validation schemas
- **`user.py`**: User-specific schemas
- **`profile.py`**: Profile-specific schemas

### 2. **Models Layer** (`app/models/`)
- **`base.py`**: Base SQLAlchemy model with common functionality
- **`user.py`**: User domain model
- **`profile.py`**: Profile domain model

### 3. **Repositories Layer** (`app/repositories/`)
- **`base.py`**: Abstract repository interfaces and base implementation
- **`user_repository.py`**: User data access implementation
- **`profile_repository.py`**: Profile data access implementation

### 4. **Services Layer** (`app/services/`)
- **`auth_service.py`**: Authentication business logic
- **`user_service.py`**: User business logic

### 5. **Routes Layer** (`app/routes/`)
- **`auth_routes.py`**: Authentication endpoints
- **`user_routes.py`**: User management endpoints

### 6. **Utils Layer** (`app/utils/`)
- **`exceptions.py`**: Custom exception classes
- **`exception_handlers.py`**: Centralized exception handling

## 📋 Implementation Details

### **Unified API Response Structure**

All endpoints return responses in this consistent format:

```json
{
  "success": bool,
  "message": str,
  "data": dict | list | null,
  "errors": [{"field": str | null, "message": str}]
}
```

### **Repository Pattern**

```python
# Abstract Interface
class IUserRepository(ABC):
    @abstractmethod
    async def get_by_email(self, email: str) -> Optional[UserResponse]:
        pass

# Concrete Implementation
class UserRepository(IUserRepository, BaseRepository):
    async def get_by_email(self, email: str) -> Optional[UserResponse]:
        # SQLAlchemy implementation
        pass
```

### **Service Layer**

```python
class AuthService:
    def __init__(self, user_repo: IUserRepository, profile_repo: IProfileRepository):
        self.user_repository = user_repo
        self.profile_repository = profile_repo
    
    async def signup(self, signup_data: SignupRequest) -> Dict[str, Any]:
        # Business logic implementation
        pass
```

### **Thin Route Layer**

```python
@router.post("/signup", response_model=ApiResponse)
async def signup(
    signup_data: SignupRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> ApiResponse:
    try:
        result = await auth_service.signup(signup_data)
        return create_success_response("User created successfully", result)
    except ConflictException as e:
        return create_error_response(e.message, [{"field": e.field, "message": e.message}])
```

## 🔧 Key Features

### **1. Dependency Injection**
- All dependencies are injected via FastAPI's `Depends()`
- Services depend on repository interfaces, not concrete implementations
- Easy to mock for testing

### **2. Centralized Exception Handling**
- Global exception handlers transform all exceptions to unified format
- Custom exception classes for different error types
- Consistent error responses across all endpoints

### **3. Repository Pattern**
- Abstract interfaces for data access
- Concrete implementations with SQLAlchemy
- Clean separation between business logic and data access

### **4. Service Layer**
- Business logic encapsulated in services
- Services depend only on repository interfaces
- Single responsibility principle applied

### **5. Thin Route Layer**
- Routes only handle HTTP concerns
- All business logic delegated to services
- Consistent response format

## 📊 Response Examples

### **Successful Signup**
```json
{
  "success": true,
  "message": "User and profile created successfully",
  "data": {
    "user": {
      "id": "uuid",
      "email": "user@example.com",
      "created_at": "2024-01-01T00:00:00Z"
    },
    "profile": {
      "id": "uuid",
      "first_name": "John",
      "last_name": "Doe",
      "account_type": "personal"
    }
  },
  "errors": []
}
```

### **Validation Error**
```json
{
  "success": false,
  "message": "Validation failed",
  "data": null,
  "errors": [
    {
      "field": "email",
      "message": "Email address format is invalid"
    }
  ]
}
```

### **Conflict Error**
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

## 🧪 Testing Strategy

### **Unit Tests**
```python
# Mock dependencies
class MockUserRepository(IUserRepository):
    async def get_by_email(self, email: str) -> Optional[UserResponse]:
        return None  # Mock implementation

# Test service in isolation
async def test_auth_service_signup():
    service = AuthService(mock_user_repo, mock_profile_repo, mock_supabase)
    result = await service.signup(signup_data)
    assert result["user"]["email"] == "test@example.com"
```

### **Integration Tests**
```python
# Test with real database
async def test_signup_endpoint():
    response = await client.post("/auth/signup", json=signup_data)
    assert response.status_code == 200
    assert response.json()["success"] is True
```

## 🚀 Benefits

### **1. Maintainability**
- Clear separation of concerns
- Easy to modify individual layers
- Consistent code structure

### **2. Testability**
- Easy to mock dependencies
- Isolated unit tests
- Clear interfaces for testing

### **3. Scalability**
- Easy to add new features
- Consistent patterns across codebase
- Reusable components

### **4. SOLID Principles**
- **Single Responsibility**: Each class has one reason to change
- **Open/Closed**: Open for extension, closed for modification
- **Liskov Substitution**: Interfaces can be substituted
- **Interface Segregation**: Focused, minimal interfaces
- **Dependency Inversion**: Depend on abstractions, not concretions

## 📁 Project Structure

```
app/
├── schemas/
│   ├── response.py          # Unified response models
│   ├── request.py           # Request validation schemas
│   ├── user.py              # User schemas
│   └── profile.py           # Profile schemas
├── models/
│   ├── base.py              # Base SQLAlchemy model
│   ├── user.py              # User domain model
│   └── profile.py           # Profile domain model
├── repositories/
│   ├── base.py              # Abstract repository interfaces
│   ├── user_repository.py   # User data access
│   └── profile_repository.py # Profile data access
├── services/
│   ├── auth_service.py      # Authentication business logic
│   └── user_service.py      # User business logic
├── routes/
│   ├── auth_routes.py       # Authentication endpoints
│   └── user_routes.py       # User management endpoints
├── utils/
│   ├── exceptions.py        # Custom exception classes
│   └── exception_handlers.py # Centralized exception handling
└── main.py                  # FastAPI application with exception handlers
```

## 🔄 Extension Guidelines

### **Adding New Endpoints**
1. Create request/response schemas in `schemas/`
2. Add repository methods in `repositories/`
3. Implement business logic in `services/`
4. Create thin route handlers in `routes/`
5. Register routes in `main.py`

### **Adding New Services**
1. Define service interface (optional)
2. Implement service with dependency injection
3. Add service to dependency providers
4. Use service in route handlers

### **Adding New Repositories**
1. Extend base repository interface
2. Implement concrete repository
3. Add repository to dependency providers
4. Use repository in services

This implementation provides a solid foundation for scalable, maintainable, and testable FastAPI applications following clean architecture principles! 🚀
