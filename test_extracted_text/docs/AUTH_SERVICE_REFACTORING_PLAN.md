# 🔧 Auth Service Refactoring Plan
## Following SOLID Principles & Separation of Concerns

---

## 🚨 Current Problems

### **1. Single Responsibility Principle (SRP) Violations**

The `AuthService` class has **10+ responsibilities**:
- Password hashing/verification
- JWT token generation/validation
- Refresh token management
- User registration logic
- User authentication logic
- Email verification logic
- Password reset logic
- Direct database queries
- Email sending
- Security logging

**Problem**: Changes to any of these concerns require modifying the same class, making it fragile and hard to maintain.

---

### **2. Dependency Inversion Principle (DIP) Violations**

**Current Code** (Lines 184-198):
```python
# ❌ Direct database queries in service
existing_user = await self.db.execute(
    select(User).where(User.email == signup_data.email)
)

existing_phone = await self.db.execute(
    select(Profile).where(Profile.phone_number == signup_data.phone_number)
)
```

**Problem**: Service depends on concrete implementation (SQLAlchemy) instead of abstraction (Repository interface).

---

### **3. Separation of Concerns Violations**

**Example from `signup()` method** (Lines 169-294):
```python
async def signup(self, signup_data: SignupRequest):
    # ❌ Data access concern
    existing_user = await self.db.execute(...)
    
    # ❌ Business logic concern
    if existing_user.scalar_one_or_none():
        raise_error_response(...)
    
    # ❌ Password hashing concern
    hashed_password = self.get_password_hash(...)
    
    # ❌ Token generation concern
    verification_token = self.email_service.generate_verification_token()
    
    # ❌ Data persistence concern
    self.db.add(user)
    await self.db.flush()
    
    # ❌ Email sending concern
    email_sent = await self.email_service.send_verification_email(...)
    
    # ❌ Response formatting concern
    return create_success_response(...)
```

**Problem**: One method handles 7 different concerns!

---

## ✅ Refactored Architecture

### **New Structure**

```
app/
├── services/
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── auth_service.py           # Orchestrates auth operations
│   │   ├── password_service.py       # Password hashing/verification
│   │   ├── token_service.py          # JWT token management
│   │   ├── refresh_token_service.py  # Refresh token management
│   │   └── verification_service.py   # Email verification logic
│   ├── auth_service.py (REFACTORED)  # Main auth orchestrator
│   └── ...
├── repositories/
│   ├── user_repository.py            # User data access
│   ├── profile_repository.py         # Profile data access
│   └── refresh_token_repository.py   # Refresh token data access
└── utils/
    ├── security/
    │   ├── password_hasher.py        # Password hashing utility
    │   └── token_generator.py        # Token generation utility
    └── ...
```

---

## 📝 Refactored Code Examples

### **1. Password Service** (Single Responsibility)

```python
# app/services/auth/password_service.py
"""Password management service - Single Responsibility"""

from passlib.context import CryptContext

class PasswordService:
    """Handles password hashing and verification only"""
    
    def __init__(self):
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    
    def hash_password(self, plain_password: str) -> str:
        """Hash a plain password"""
        return self.pwd_context.hash(plain_password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
```

---

### **2. Token Service** (Single Responsibility)

```python
# app/services/auth/token_service.py
"""JWT token management service - Single Responsibility"""

from jose import jwt, JWTError
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import os

class TokenService:
    """Handles JWT token generation and validation only"""
    
    def __init__(self):
        self.secret_key = os.getenv("SECRET_KEY", "your-secret-key")
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 15
    
    def create_access_token(
        self, 
        data: Dict[str, Any], 
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """Generate JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        return jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except JWTError:
            return None
```

---

### **3. Refresh Token Service** (Single Responsibility)

```python
# app/services/auth/refresh_token_service.py
"""Refresh token management service - Single Responsibility"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession

from ...repositories.refresh_token_repository import RefreshTokenRepository
from ...models.refresh_token import RefreshToken

class RefreshTokenService:
    """Handles refresh token operations only"""
    
    def __init__(self, refresh_token_repository: RefreshTokenRepository):
        self.repository = refresh_token_repository
        self.expire_days = 7
    
    def generate_token(self) -> str:
        """Generate a secure refresh token"""
        return secrets.token_urlsafe(32)
    
    def hash_token(self, token: str) -> str:
        """Hash token for secure storage"""
        return hashlib.sha256(token.encode()).hexdigest()
    
    async def create_refresh_token(
        self, 
        db: AsyncSession,
        user_id: int, 
        token: str
    ) -> RefreshToken:
        """Create and store refresh token"""
        token_hash = self.hash_token(token)
        expires_at = datetime.utcnow() + timedelta(days=self.expire_days)
        
        return await self.repository.create(
            db=db,
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at
        )
    
    async def validate_token(
        self, 
        db: AsyncSession,
        token: str
    ) -> Optional[RefreshToken]:
        """Validate refresh token"""
        token_hash = self.hash_token(token)
        return await self.repository.get_valid_token(db, token_hash)
    
    async def revoke_token(self, db: AsyncSession, token: str) -> bool:
        """Revoke a refresh token"""
        token_hash = self.hash_token(token)
        return await self.repository.revoke_token(db, token_hash)
    
    async def revoke_all_user_tokens(self, db: AsyncSession, user_id: int) -> int:
        """Revoke all tokens for a user"""
        return await self.repository.revoke_all_user_tokens(db, user_id)
```

---

### **4. Refactored Auth Service** (Orchestrator)

```python
# app/services/auth_service.py (REFACTORED)
"""
Authentication orchestration service.

This service orchestrates authentication operations by coordinating
between multiple specialized services and repositories.
"""

from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta

from .auth.password_service import PasswordService
from .auth.token_service import TokenService
from .auth.refresh_token_service import RefreshTokenService
from .email_service import EmailService
from ..repositories.user_repository import UserRepository
from ..repositories.profile_repository import ProfileRepository
from ..models.user import User
from ..models.profile import Profile
from ..models.role import DEFAULT_USER_ROLE
from ..schemas.request import SignupRequest, LoginRequest
from ..schemas.response import create_success_response, raise_error_response
from ..config.enhanced_logging import get_logger, log_auth_attempt, mask_email
from ..utils.api_exceptions import ApiException

logger = get_logger(__name__)

class AuthService:
    """
    Authentication orchestration service.
    
    Coordinates between specialized services to handle authentication operations.
    Follows Single Responsibility Principle and Dependency Inversion Principle.
    """
    
    def __init__(
        self,
        db: AsyncSession,
        user_repository: UserRepository,
        profile_repository: ProfileRepository,
        password_service: PasswordService,
        token_service: TokenService,
        refresh_token_service: RefreshTokenService,
        email_service: EmailService,
        correlation_id: Optional[str] = None
    ):
        self.db = db
        self.user_repository = user_repository
        self.profile_repository = profile_repository
        self.password_service = password_service
        self.token_service = token_service
        self.refresh_token_service = refresh_token_service
        self.email_service = email_service
        self.correlation_id = correlation_id
        self.logger = get_logger(__name__, correlation_id)
    
    async def signup(self, signup_data: SignupRequest) -> Dict[str, Any]:
        """
        Register a new user.
        
        Orchestrates:
        - User existence check (via repository)
        - Password hashing (via password service)
        - User creation (via repository)
        - Profile creation (via repository)
        - Email verification (via email service)
        """
        try:
            # 1. Check if user exists (via repository)
            if await self.user_repository.email_exists(self.db, signup_data.email):
                self.logger.warning(f"Signup attempt with existing email: {mask_email(signup_data.email)}")
                raise_error_response(
                    status_code=422,
                    message="Email already registered",
                    field="email"
                )
            
            # 2. Check phone number if provided (via repository)
            if signup_data.phone_number:
                if await self.profile_repository.phone_exists(self.db, signup_data.phone_number):
                    self.logger.warning(f"Signup attempt with existing phone")
                    raise_error_response(
                        status_code=422,
                        message="Phone number is already registered",
                        field="phone_number"
                    )
            
            # 3. Hash password (via password service)
            hashed_password = self.password_service.hash_password(signup_data.password)
            
            # 4. Generate verification token (via email service)
            verification_token = self.email_service.generate_verification_token()
            verification_expires = datetime.utcnow() + timedelta(hours=24)
            
            # 5. Create user (via repository)
            user = await self.user_repository.create_user(
                db=self.db,
                email=signup_data.email,
                password_hash=hashed_password,
                verification_token=verification_token,
                verification_expires=verification_expires,
                role=DEFAULT_USER_ROLE
            )
            
            # 6. Create profile (via repository)
            profile = await self.profile_repository.create_profile(
                db=self.db,
                user_id=user.id,
                email=signup_data.email,
                first_name=signup_data.first_name,
                last_name=signup_data.last_name,
                phone_number=signup_data.phone_number,
                account_type=signup_data.account_type
            )
            
            # 7. Send verification email (via email service)
            email_sent = False
            try:
                user_name = f"{signup_data.first_name} {signup_data.last_name}"
                email_sent = await self.email_service.send_verification_email(
                    to_email=signup_data.email,
                    user_name=user_name,
                    verification_token=verification_token
                )
                
                if email_sent:
                    await self.user_repository.mark_email_sent(self.db, user.id)
                    
            except Exception as e:
                self.logger.error(f"Failed to send verification email: {str(e)}")
            
            self.logger.info(f"User registered successfully: {mask_email(user.email)}")
            
            return create_success_response(
                message="User registered successfully",
                data={
                    "email": user.email,
                    "verification_required": True,
                    "email_sent": email_sent
                }
            )
            
        except ApiException:
            raise
        except Exception as e:
            await self.db.rollback()
            self.logger.error(f"User registration failed: {str(e)}")
            raise_error_response(
                status_code=500,
                message="User registration failed",
                field="email"
            )
    
    async def login(self, login_data: LoginRequest) -> Dict[str, Any]:
        """
        Authenticate a user.
        
        Orchestrates:
        - User lookup (via repository)
        - Password verification (via password service)
        - Account status checks
        - Token generation (via token services)
        - Profile retrieval (via repository)
        """
        try:
            # 1. Find user (via repository)
            user = await self.user_repository.get_by_email(self.db, login_data.email)
            
            if not user:
                log_auth_attempt(self.logger, login_data.email, False, 
                               self.correlation_id, reason="user_not_found")
                raise_error_response(
                    status_code=401,
                    message="Invalid email or password",
                    field="email"
                )
            
            # 2. Check account lock status
            if user.locked_until and user.locked_until > datetime.utcnow():
                remaining_minutes = int((user.locked_until - datetime.utcnow()).total_seconds() / 60)
                raise_error_response(
                    status_code=429,
                    message=f"Account locked. Try again in {remaining_minutes} minutes.",
                    field="email"
                )
            
            # 3. Verify password (via password service)
            if not self.password_service.verify_password(login_data.password, user.password_hash):
                # Increment failed attempts (via repository)
                await self.user_repository.increment_failed_attempts(self.db, user.id)
                
                log_auth_attempt(self.logger, login_data.email, False,
                               self.correlation_id, reason="invalid_password")
                
                raise_error_response(
                    status_code=401,
                    message="Invalid email or password",
                    field="email"
                )
            
            # 4. Check account status
            if not user.is_active:
                raise_error_response(
                    status_code=401,
                    message="Account is deactivated",
                    field="email"
                )
            
            if not user.is_verified:
                raise_error_response(
                    status_code=401,
                    message="Email not verified",
                    field="email"
                )
            
            # 5. Reset failed attempts (via repository)
            await self.user_repository.reset_failed_attempts(self.db, user.id)
            
            # 6. Get profile (via repository)
            profile = await self.profile_repository.get_by_user_id(self.db, user.id)
            
            # 7. Generate tokens (via token services)
            access_token = self.token_service.create_access_token({
                "sub": str(user.id),
                "email": user.email,
                "role": user.role
            })
            
            refresh_token = self.refresh_token_service.generate_token()
            await self.refresh_token_service.create_refresh_token(
                self.db, user.id, refresh_token
            )
            
            log_auth_attempt(self.logger, login_data.email, True, 
                           self.correlation_id, user_id=user.id)
            
            return create_success_response(
                message="Login successful",
                data={
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "role": user.role
                    },
                    "profile": {
                        "first_name": profile.first_name if profile else None,
                        "last_name": profile.last_name if profile else None
                    } if profile else None,
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "token_type": "bearer"
                }
            )
            
        except ApiException:
            raise
        except Exception as e:
            self.logger.error(f"Login failed: {str(e)}")
            raise_error_response(
                status_code=500,
                message="Login failed",
                field="email"
            )
```

---

### **5. Repository Layer** (Data Access Abstraction)

```python
# app/repositories/user_repository.py (ENHANCED)
"""User repository with additional methods for auth operations"""

from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timedelta

from ..models.user import User
from .base import BaseRepository

class UserRepository(BaseRepository):
    """Repository for user data access operations"""
    
    def __init__(self, db: AsyncSession):
        super().__init__(db, User)
    
    async def get_by_email(self, db: AsyncSession, email: str) -> Optional[User]:
        """Get user by email"""
        result = await db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def email_exists(self, db: AsyncSession, email: str) -> bool:
        """Check if email already exists"""
        user = await self.get_by_email(db, email)
        return user is not None
    
    async def create_user(
        self,
        db: AsyncSession,
        email: str,
        password_hash: str,
        verification_token: str,
        verification_expires: datetime,
        role: str
    ) -> User:
        """Create a new user"""
        user = User(
            email=email,
            password_hash=password_hash,
            is_active=True,
            is_verified=False,
            verification_token=verification_token,
            verification_token_expires=verification_expires,
            failed_attempts=0,
            email_sent=False,
            role=role
        )
        
        db.add(user)
        await db.commit()
        await db.refresh(user)
        
        return user
    
    async def increment_failed_attempts(self, db: AsyncSession, user_id: int) -> None:
        """Increment failed login attempts"""
        user = await self.get_by_id(db, user_id)
        if user:
            user.failed_attempts += 1
            
            # Lock account if max attempts reached
            if user.failed_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=30)
            
            await db.commit()
    
    async def reset_failed_attempts(self, db: AsyncSession, user_id: int) -> None:
        """Reset failed login attempts"""
        user = await self.get_by_id(db, user_id)
        if user:
            user.failed_attempts = 0
            user.locked_until = None
            user.last_login = datetime.utcnow()
            await db.commit()
    
    async def mark_email_sent(self, db: AsyncSession, user_id: int) -> None:
        """Mark verification email as sent"""
        user = await self.get_by_id(db, user_id)
        if user:
            user.email_sent = True
            user.email_sent_at = datetime.utcnow()
            await db.commit()
```

---

## 🎯 Benefits of Refactored Architecture

### **1. Single Responsibility Principle ✅**
- Each service has ONE reason to change
- `PasswordService` → Only password operations
- `TokenService` → Only JWT operations
- `RefreshTokenService` → Only refresh token operations
- `AuthService` → Only orchestration

### **2. Dependency Inversion Principle ✅**
- Services depend on abstractions (repositories)
- No direct database queries in services
- Easy to swap implementations

### **3. Open/Closed Principle ✅**
- Add new auth methods by extending, not modifying
- Can add OAuth without touching existing code

### **4. Separation of Concerns ✅**
- Clear boundaries between layers
- Easy to test each component independently
- Changes are isolated

### **5. Testability ✅**
```python
# Easy to test with mocks
def test_login():
    # Mock repositories
    mock_user_repo = Mock(UserRepository)
    mock_profile_repo = Mock(ProfileRepository)
    
    # Mock services
    mock_password_service = Mock(PasswordService)
    mock_token_service = Mock(TokenService)
    
    # Create auth service with mocks
    auth_service = AuthService(
        db=mock_db,
        user_repository=mock_user_repo,
        profile_repository=mock_profile_repo,
        password_service=mock_password_service,
        token_service=mock_token_service,
        ...
    )
    
    # Test login
    result = await auth_service.login(login_data)
    assert result["success"] == True
```

---

## 📊 Comparison

### **Before (Current)**
```
AuthService (951 lines)
├── 10+ responsibilities
├── Direct database access
├── Hard to test
├── Tightly coupled
└── Fragile (changes ripple everywhere)
```

### **After (Refactored)**
```
PasswordService (50 lines)
├── Password hashing/verification only
└── Easy to test

TokenService (80 lines)
├── JWT generation/validation only
└── Easy to test

RefreshTokenService (120 lines)
├── Refresh token management only
└── Easy to test

AuthService (300 lines - Orchestrator)
├── Coordinates operations
├── Uses repositories (DIP)
├── Single responsibility (orchestration)
└── Easy to test with mocks

UserRepository (200 lines)
├── User data access only
└── Abstraction layer

ProfileRepository (150 lines)
├── Profile data access only
└── Abstraction layer
```

---

## 🚀 Migration Strategy

### **Phase 1: Create New Services** (1-2 days)
1. Create `PasswordService`
2. Create `TokenService`
3. Create `RefreshTokenService`
4. Add tests for each service

### **Phase 2: Enhance Repositories** (1 day)
1. Add missing methods to `UserRepository`
2. Add missing methods to `ProfileRepository`
3. Create `RefreshTokenRepository`

### **Phase 3: Refactor AuthService** (2-3 days)
1. Update dependency injection
2. Refactor `signup()` method
3. Refactor `login()` method
4. Refactor other methods
5. Update tests

### **Phase 4: Update Router** (1 day)
1. Update `auth_routes.py` dependency injection
2. Test all endpoints
3. Update documentation

---

## ✅ Action Items

1. **Review this plan** with team
2. **Create new service classes** following SRP
3. **Enhance repository layer** with auth-specific methods
4. **Refactor AuthService** to be an orchestrator
5. **Update dependency injection** in router
6. **Add comprehensive tests** for each component
7. **Update documentation**

---

## 📚 Resources

- [SOLID Principles](https://en.wikipedia.org/wiki/SOLID)
- [Clean Architecture by Robert Martin](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [Dependency Injection in Python](https://python-dependency-injector.ets-labs.org/)

