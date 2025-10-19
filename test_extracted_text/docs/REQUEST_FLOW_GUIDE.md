# 🔄 Complete Request Flow Guide
## From Frontend API Call to Backend Response

This guide explains the complete journey of an HTTP request through your FastAPI application.

---

## 📋 Table of Contents
1. [Request Flow Overview](#request-flow-overview)
2. [Detailed Flow Example: Login Endpoint](#detailed-flow-example-login-endpoint)
3. [Layer-by-Layer Explanation](#layer-by-layer-explanation)
4. [Error Handling Flow](#error-handling-flow)
5. [Response Flow](#response-flow)

---

## 🎯 Request Flow Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND APPLICATION                             │
│  (React/Vue/Angular - runs on http://localhost:3000)                   │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                │ 1. HTTP Request (POST /api/v1/auth/login)
                                │    Headers: { Content-Type: application/json }
                                │    Body: { email, password }
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      ENTRY POINT (run.py / start_server.py)             │
│  • Starts Uvicorn ASGI server on http://127.0.0.1:8000                 │
│  • Loads app from app.main:app                                          │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                      FASTAPI APPLICATION (app/main.py)                   │
│  2. Request reaches FastAPI app                                          │
│     • CORS middleware checks origin                                      │
│     • Generates correlation ID for request tracing                       │
│     • Logging middleware logs request                                    │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   ROUTER LAYER (app/routes/auth_routes.py)               │
│  3. Route matching: POST /api/v1/auth/login                              │
│     • Pydantic validates request body (LoginRequest schema)              │
│     • Extracts email & password                                          │
│     • Dependency injection starts                                        │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              DEPENDENCY INJECTION (app/db/database.py)                   │
│  4. Dependencies are resolved:                                           │
│     • get_db() → Creates database session (AsyncSession)                 │
│     • get_auth_service(db) → Creates AuthService instance                │
│     • Request object → Passed to service for correlation ID              │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│           SERVICE LAYER (app/services/auth_service.py)                   │
│  5. Business logic execution:                                            │
│     a. Validate input data                                               │
│     b. Query database for user (via SQLAlchemy)                          │
│     c. Verify password hash                                              │
│     d. Check account status (locked, active, etc.)                       │
│     e. Generate JWT access token                                         │
│     f. Generate refresh token                                            │
│     g. Log authentication attempt                                        │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│            REPOSITORY LAYER (app/repositories/user_repository.py)        │
│  6. Data access:                                                         │
│     • Repository abstracts database queries                              │
│     • Executes SELECT query via SQLAlchemy ORM                           │
│     • Returns User model instance                                        │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   DATABASE LAYER (app/db/database.py)                    │
│  7. Database operations:                                                 │
│     • SQLAlchemy creates SQL query                                       │
│     • Executes against SQLite database (app.db)                          │
│     • Returns raw data                                                   │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    MODEL LAYER (app/models/user.py)                      │
│  8. Data mapping:                                                        │
│     • SQLAlchemy ORM maps database rows to Python objects                │
│     • User model instance created with attributes                        │
│     • Relationships loaded (profile, subscriptions, etc.)                │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                │ ◄─── Data flows back up ───
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│           SERVICE LAYER - Response Preparation                           │
│  9. Service processes result:                                            │
│     • Creates tokens (JWT access + refresh token)                        │
│     • Saves refresh token to database                                    │
│     • Prepares response data                                             │
│     • Uses Pydantic schema (ApiResponse) to format output                │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                SCHEMA LAYER (app/schemas/response.py)                    │
│  10. Response validation:                                                │
│      • ApiResponse schema validates response structure                   │
│      • Ensures consistent format:                                        │
│        {                                                                 │
│          "success": true,                                                │
│          "message": "Login successful",                                  │
│          "data": { user, tokens, profile },                              │
│          "errors": []                                                    │
│        }                                                                 │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                   ROUTER LAYER - Response Return                         │
│  11. Router returns response:                                            │
│      • FastAPI serializes Pydantic model to JSON                         │
│      • Sets HTTP status code (200 OK)                                    │
│      • Sets response headers                                             │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│              MIDDLEWARE LAYER - Final Processing                         │
│  12. Response middleware:                                                │
│      • CORS headers added                                                │
│      • Logging middleware logs response                                  │
│      • Correlation ID added to response headers                          │
└───────────────────────────────┬─────────────────────────────────────────┘
                                │
                                │ 13. HTTP Response
                                │     Status: 200 OK
                                │     Headers: { Content-Type: application/json }
                                │     Body: JSON response
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND APPLICATION                             │
│  14. Frontend receives response:                                         │
│      • Parses JSON                                                       │
│      • Stores tokens in localStorage/cookies                             │
│      • Updates UI state                                                  │
│      • Redirects to dashboard                                            │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 📝 Detailed Flow Example: Login Endpoint

### **Step 1: Frontend Sends Request**

```javascript
// Frontend (React/Vue/Angular)
fetch('http://127.0.0.1:8000/api/v1/auth/login', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email: 'user@example.com',
    password: 'SecurePassword123!'
  })
})
```

### **Step 2: Entry Point (run.py)**

```python
# run.py
import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "app.main:app",  # ← Loads FastAPI app
        host="127.0.0.1",
        port=8000,
        reload=True
    )
```

**What happens:**
- Uvicorn starts ASGI server
- Loads `app` object from `app/main.py`
- Listens on port 8000

### **Step 3: FastAPI App Initialization (app/main.py)**

```python
# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="SQLite Auth FastAPI",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Frontend can access
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
from .routes.auth_routes import router as auth_routes
app.include_router(auth_routes)  # ← Registers /api/v1/auth/* routes
```

**What happens:**
- Request passes through CORS middleware
- Route matching finds: `POST /api/v1/auth/login`
- Forwards to auth_routes router

### **Step 4: Router Layer (app/routes/auth_routes.py)**

```python
# app/routes/auth_routes.py
from fastapi import APIRouter, Depends
from ..services.auth_service import AuthService
from ..schemas.request import LoginRequest
from ..schemas.response import ApiResponse

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication"])

def get_auth_service(db: AsyncSession = Depends(get_db)) -> AuthService:
    """Dependency injection for AuthService"""
    return AuthService(db)

@router.post("/login", response_model=ApiResponse)
async def login(
    login_data: LoginRequest,  # ← Pydantic validates input
    auth_service: AuthService = Depends(get_auth_service)  # ← DI
) -> ApiResponse:
    """Login endpoint"""
    return await auth_service.login(login_data)
```

**What happens:**
1. **Pydantic Validation**: `LoginRequest` schema validates:
   ```python
   class LoginRequest(BaseModel):
       email: EmailStr  # ← Validates email format
       password: str    # ← Required field
   ```
2. **Dependency Injection**:
   - `get_db()` creates database session
   - `get_auth_service(db)` creates AuthService instance
3. **Calls service method**: `auth_service.login(login_data)`

### **Step 5: Service Layer (app/services/auth_service.py)**

```python
# app/services/auth_service.py
class AuthService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repository = UserRepository(db)
    
    async def login(self, login_data: LoginRequest) -> ApiResponse:
        """Business logic for login"""
        
        # 1. Find user by email (via repository)
        user = await self.user_repository.get_by_email(login_data.email)
        
        if not user:
            # Raise error (handled by exception handlers)
            raise ApiException(
                status_code=401,
                payload={
                    "success": False,
                    "message": "Invalid credentials",
                    "data": None,
                    "errors": [{"field": "email", "message": "User not found"}]
                }
            )
        
        # 2. Verify password
        if not self.verify_password(login_data.password, user.password_hash):
            raise ApiException(status_code=401, payload={...})
        
        # 3. Check if account is locked
        if user.is_locked:
            raise ApiException(status_code=403, payload={...})
        
        # 4. Generate tokens
        access_token = self.create_access_token({"sub": str(user.id)})
        refresh_token = self.generate_refresh_token()
        
        # 5. Save refresh token
        await self.create_refresh_token_record(user.id, refresh_token)
        
        # 6. Get user profile
        profile = await self.user_repository.get_profile(user.id)
        
        # 7. Create success response
        return create_success_response(
            message="Login successful",
            data={
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "role": user.role
                },
                "tokens": {
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer"
                },
                "profile": profile
            }
        )
```

**What happens:**
- Business logic validates credentials
- Database queries through repository
- Tokens generated
- Response formatted using helper function

### **Step 6: Repository Layer (app/repositories/user_repository.py)**

```python
# app/repositories/user_repository.py
class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db
    
    async def get_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
```

**What happens:**
- Repository abstracts database access
- Uses SQLAlchemy to build SQL query
- Returns User model instance

### **Step 7: Database Layer (SQLAlchemy ORM)**

```python
# Generated SQL Query
SELECT users.id, users.email, users.password_hash, users.role
FROM users
WHERE users.email = 'user@example.com'
```

**What happens:**
- SQLAlchemy converts Python code to SQL
- Executes query against `app.db` (SQLite)
- Returns database row

### **Step 8: Model Layer (app/models/user.py)**

```python
# app/models/user.py
from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(String, default="user")
    is_locked = Column(Boolean, default=False)
    
    # Relationships
    profile = relationship("Profile", back_populates="user")
    refresh_tokens = relationship("RefreshToken", back_populates="user")
```

**What happens:**
- SQLAlchemy maps database row to Python object
- Creates User instance with all attributes
- Loads relationships if needed

### **Step 9: Response Schema (app/schemas/response.py)**

```python
# app/schemas/response.py
class ApiResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    errors: List[ErrorDetail] = []

def create_success_response(message: str, data: Any) -> ApiResponse:
    """Helper to create success response"""
    return ApiResponse(
        success=True,
        message=message,
        data=data,
        errors=[]
    )
```

**What happens:**
- Response formatted to unified structure
- Pydantic validates response format
- Ensures consistency across all endpoints

### **Step 10: Response Returned to Frontend**

```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "user": {
      "id": 1,
      "email": "user@example.com",
      "role": "user"
    },
    "tokens": {
      "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
      "refresh_token": "7Kj9mP2nQ8rT1vX4yZ...",
      "token_type": "bearer"
    },
    "profile": {
      "first_name": "John",
      "last_name": "Doe",
      "avatar_url": null
    }
  },
  "errors": []
}
```

---

## 🔧 Layer-by-Layer Explanation

### **1. Entry Point Layer**
**Files**: `run.py`, `start_server.py`

**Purpose**: Start the application server

**Responsibilities**:
- Initialize Uvicorn ASGI server
- Load FastAPI app
- Set host, port, and reload options

---

### **2. Application Layer**
**Files**: `app/main.py`

**Purpose**: Configure FastAPI application

**Responsibilities**:
- Create FastAPI instance
- Register middleware (CORS, logging)
- Include routers
- Register exception handlers
- Setup database on startup

---

### **3. Router Layer**
**Files**: `app/routes/*.py`

**Purpose**: Define API endpoints

**Responsibilities**:
- Map HTTP methods to functions
- Define URL paths
- Handle request/response
- Validate input with Pydantic
- Dependency injection
- Minimal business logic (delegate to services)

**Example routers**:
- `auth_routes.py` → `/api/v1/auth/*`
- `user_routes.py` → `/api/v1/users/*`
- `legal_assistant_router.py` → `/api/v1/legal-assistant/*`

---

### **4. Service Layer**
**Files**: `app/services/*.py`

**Purpose**: Implement business logic

**Responsibilities**:
- Validate business rules
- Orchestrate operations
- Call repositories for data
- Process data transformations
- Generate tokens/emails
- Log important events
- Return formatted responses

**Example services**:
- `AuthService` → Authentication logic
- `UserService` → User management
- `LegalAssistantService` → AI chat logic

---

### **5. Repository Layer**
**Files**: `app/repositories/*.py`

**Purpose**: Abstract database access

**Responsibilities**:
- CRUD operations (Create, Read, Update, Delete)
- Database queries
- Data filtering and sorting
- Return model instances
- No business logic

**Example repositories**:
- `UserRepository` → User database operations
- `ProfileRepository` → Profile database operations
- `LegalDocumentRepository` → Document database operations

---

### **6. Database Layer**
**Files**: `app/db/database.py`

**Purpose**: Database connection management

**Responsibilities**:
- Create database engine
- Manage sessions
- Create tables on startup
- Provide `get_db()` dependency

---

### **7. Model Layer**
**Files**: `app/models/*.py`

**Purpose**: Define database schema

**Responsibilities**:
- SQLAlchemy ORM models
- Table definitions
- Column types and constraints
- Relationships between tables
- No business logic

**Example models**:
- `User` → users table
- `Profile` → profiles table
- `LegalDocument` → legal_documents table

---

### **8. Schema Layer**
**Files**: `app/schemas/*.py`

**Purpose**: Validate request/response data

**Responsibilities**:
- Pydantic models for validation
- Request schemas (input)
- Response schemas (output)
- Data transformation
- Type hints

**Example schemas**:
- `LoginRequest` → Validates login input
- `ApiResponse` → Formats all responses
- `UserResponse` → User data output

---

### **9. Utility Layer**
**Files**: `app/utils/*.py`

**Purpose**: Helper functions and middleware

**Responsibilities**:
- Authentication helpers (JWT)
- Exception handlers
- Encryption utilities
- Logging utilities
- Custom exceptions

---

### **10. Configuration Layer**
**Files**: `app/config/*.py`

**Purpose**: Application configuration

**Responsibilities**:
- Environment variables
- Logging setup
- URL configuration
- API keys and settings

---

## ⚠️ Error Handling Flow

### **Error Flow Diagram**

```
┌──────────────────────────────────────────────────┐
│  Service raises exception                         │
│  (ApiException, ValidationException, etc.)        │
└────────────────┬─────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────┐
│  Exception bubbles up to router                   │
│  (router catches or re-raises)                    │
└────────────────┬─────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────┐
│  Global Exception Handler                         │
│  (app/utils/exception_handlers.py)                │
│                                                    │
│  • Matches exception type                         │
│  • Formats to ApiResponse                         │
│  • Logs error with correlation ID                 │
│  • Returns appropriate HTTP status                │
└────────────────┬─────────────────────────────────┘
                 │
                 ▼
┌──────────────────────────────────────────────────┐
│  JSON Error Response                              │
│  {                                                │
│    "success": false,                              │
│    "message": "Invalid credentials",              │
│    "data": null,                                  │
│    "errors": [                                    │
│      {"field": "email", "message": "User not found"}│
│    ]                                              │
│  }                                                │
└──────────────────────────────────────────────────┘
```

### **Example Error Handler**

```python
# app/utils/exception_handlers.py
@app.exception_handler(ApiException)
async def api_exception_handler(request: Request, exc: ApiException):
    """Handle custom API exceptions"""
    logger.error(f"API Exception: {exc.payload}")
    
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.payload
    )
```

---

## ✅ Response Flow

### **Success Response Structure**

Every successful response follows this structure:

```json
{
  "success": true,
  "message": "Operation successful",
  "data": { /* actual response data */ },
  "errors": []
}
```

### **Error Response Structure**

Every error response follows this structure:

```json
{
  "success": false,
  "message": "Operation failed",
  "data": null,
  "errors": [
    {
      "field": "field_name",
      "message": "Error description"
    }
  ]
}
```

---

## 🎯 Key Concepts

### **1. Dependency Injection**
FastAPI automatically resolves dependencies:

```python
# FastAPI injects these automatically
async def endpoint(
    db: AsyncSession = Depends(get_db),        # ← Database session
    auth_service: AuthService = Depends(...)   # ← Service instance
):
    pass
```

### **2. Async/Await**
All database operations are asynchronous:

```python
# Async functions
async def get_user(db: AsyncSession, user_id: int):
    result = await db.execute(...)  # ← Wait for database
    return result.scalar_one_or_none()
```

### **3. Middleware**
Processes requests/responses globally:

```python
# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"]
)
```

### **4. Pydantic Validation**
Automatic data validation:

```python
class LoginRequest(BaseModel):
    email: EmailStr        # ← Validates email format
    password: constr(min_length=8)  # ← Validates length
```

---

## 📚 Complete Request Example: Legal Assistant Chat

Let's trace a more complex example:

```
Frontend Request:
POST /api/v1/legal-assistant/chat
Body: { "question": "ما هي حقوقي في عقد العمل؟", "history": [...] }

↓
1. Router: legal_assistant_router.py
   - Validates ChatRequest schema
   - Injects LegalDocumentRepository
   - Calls LegalAssistantService.process_chat_request()

↓
2. Service: legal_assistant_service.py
   - Detects language (Arabic)
   - Uses repository to get document chunks with embeddings
   - Calculates similarity scores
   - Calls OpenAI API
   - Formats response

↓
3. Repository: legal_document_repository.py
   - Queries legal_document_chunks table
   - Filters by embedding existence
   - Returns LegalDocumentChunk models

↓
4. External API: OpenAI
   - Sends prompt with context
   - Receives AI-generated answer
   
↓
5. Response Formation:
   - Creates ChatResponse schema
   - Includes answer, sources, quality score
   - Returns to frontend

↓
Frontend Receives:
{
  "answer": "حقوقك في عقد العمل تشمل...",
  "chunks_used": 5,
  "sources": ["نظام العمل السعودي"],
  "quality_score": "high"
}
```

---

## 🔍 Debugging Tips

### **1. Follow the Correlation ID**
Every request has a correlation ID for tracing:

```python
# In logs:
[correlation-id-abc123] Request received
[correlation-id-abc123] Database query executed
[correlation-id-abc123] Response sent
```

### **2. Check Logs**
Logs are in `logs/` directory:
- `app.log` - All application logs
- `errors.log` - Error logs only

### **3. Use /docs**
FastAPI auto-generates API documentation:
- Visit `http://127.0.0.1:8000/docs`
- Test endpoints directly
- See request/response schemas

---

## 🎓 Summary

**Request Flow in 5 Steps:**

1. **Frontend** → Sends HTTP request
2. **Router** → Validates input, injects dependencies
3. **Service** → Executes business logic
4. **Repository** → Accesses database
5. **Response** → Formatted and returned to frontend

**Key Principles:**
- **Separation of Concerns**: Each layer has specific responsibility
- **Dependency Injection**: Automatic resolution of dependencies
- **Unified Response**: All endpoints return same structure
- **Error Handling**: Consistent error format across all endpoints
- **Async Operations**: Non-blocking database and API calls

---

**Next Steps:**
- Read `docs/APPLICATION_STRUCTURE.md` for architecture overview
- Check `docs/API_DOCUMENTATION.md` for endpoint details
- See `docs/CLEAN_ARCHITECTURE_IMPLEMENTATION.md` for design patterns

