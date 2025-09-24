# Application Structure Documentation

## 📁 Project Overview

This is a **FastAPI-based backend application** integrated with **Supabase Authentication** and **PostgreSQL database**. The application provides a comprehensive subscription management system with user profiles, billing, and usage tracking.

---

## 🏗️ Root Directory Structure

```
my_project/
├── 📁 app/                          # Main application package
├── 📁 docs/                         # Documentation and schemas
├── 📁 tests/                        # Test files
├── 📁 alembic/                      # Database migrations
├── 📄 requirements.txt              # Python dependencies
├── 📄 README.md                     # Project documentation
├── 📄 run.py                        # Main server runner
├── 📄 start_server.py               # Alternative server runner
├── 📄 supabase.env                  # Environment configuration
├── 📄 alembic.ini                   # Alembic configuration
└── 📄 API_DOCUMENTATION.md          # API endpoint documentation
```

---

## 📦 Application Package (`app/`)

### 🎯 Core Application Files

#### `main.py` - Application Entry Point
- **Purpose**: FastAPI application initialization and configuration
- **Features**:
  - CORS middleware configuration
  - Router registration
  - Database table creation on startup
  - Health check endpoints
  - Server information endpoints

#### `__init__.py` - Package Initialization
- Makes `app/` a Python package

---

### 🔧 Configuration (`app/config/`)

#### `supabase.py` - Supabase Configuration
```python
# Key Components:
- SUPABASE_URL: Supabase project URL
- SUPABASE_ANON_KEY: Anonymous key for client operations
- get_supabase_client(): Factory function for Supabase client
- Global supabase client instance
```

**Purpose**: Centralized Supabase client management and configuration

---

### 🗄️ Database Layer (`app/db/`)

#### `database.py` - Database Configuration
```python
# Key Components:
- DATABASE_URL: PostgreSQL connection string
- AsyncEngine: SQLAlchemy async engine
- AsyncSessionLocal: Session factory
- Base: Declarative base for models
- get_db(): Dependency for database sessions
- create_tables(): Table creation function
```

**Purpose**: Database connection management and session handling

#### `models.py` - Database Models Registry
- Imports all model classes to ensure they're registered with SQLAlchemy
- Required for proper table creation and relationships

---

### 📊 Data Models (`app/models/`)

#### `profile.py` - User Profile Model
```python
class Profile(Base):
    # Fields:
    - id: UUID (Primary Key, references auth.users.id)
    - first_name: Text (required)
    - last_name: Text (required)
    - avatar_url: Text (Optional)
    - phone_number:Text (required)
    - account_type: Enum(AccountType) (Default: PERSONAL)
    - created_at: DateTime (Auto-generated)
    - updated_at: DateTime (Auto-updated)

# Enums:
- AccountType: PERSONAL, BUSINESS
```

#### `plan.py` - Subscription Plan Model
```python
class Plan(Base):
    # Fields:
    - plan_id: UUID (Primary Key)
    - plan_name: Text (e.g., "Free Trial", "Basic Monthly")
    - plan_type: Text (free, monthly, annual)
    - price: Numeric(10,2) (Price in SAR)
    - billing_cycle: Text (monthly, yearly, none)
    - file_limit: Integer (File upload limit)
    - ai_message_limit: Integer (AI chat limit)
    - contract_limit: Integer (Contract limit)
    - report_limit: Integer (Report export limit)
    - token_limit: Integer (Token usage limit)
    - multi_user_limit: Integer (Team member limit)
    - government_integration: Boolean (Government features)
    - description: Text (Plan description)
    - is_active: Boolean (Plan availability)
    
    # Relationships:
    - subscriptions: One-to-Many with Subscription
```

#### `subscription.py` - Subscription Model
```python
class Subscription(Base):
    # Fields:
    - subscription_id: UUID (Primary Key)
    - user_id: UUID (Foreign Key to Profile.id)
    - plan_id: UUID (Foreign Key to Plan.plan_id)
    - start_date: DateTime (Subscription start)
    - end_date: DateTime (Subscription end)
    - auto_renew: Boolean (Auto-renewal setting)
    - status: Enum(StatusType) (ACTIVE, EXPIRED, CANCELLED)
    - current_usage: JSONB (Feature usage tracking)
    
    # Enums:
    - StatusType: ACTIVE, EXPIRED, CANCELLED
    
    # Relationships:
    - user: Many-to-One with Profile
    - plan: Many-to-One with Plan
    - usage_tracking: One-to-Many with UsageTracking
    - billing: One-to-Many with Billing
```

#### `usage_tracking.py` - Usage Tracking Model
```python
class UsageTracking(Base):
    # Fields:
    - usage_id: UUID (Primary Key)
    - subscription_id: UUID (Foreign Key to Subscription)
    - feature: Text (Feature name: file_upload, ai_chat, etc.)
    - used_count: Integer (Current usage count)
    - reset_cycle: Text (daily, monthly, yearly)
    - last_reset: DateTime (Last reset timestamp)
    
    # Relationships:
    - subscription: Many-to-One with Subscription
```

#### `billing.py` - Billing Model
```python
class Billing(Base):
    # Fields:
    - invoice_id: UUID (Primary Key)
    - subscription_id: UUID (Foreign Key to Subscription)
    - amount: Numeric(10,2) (Invoice amount)
    - currency: Text (Default: "SAR")
    - status: Text (paid, pending, failed, refunded)
    - invoice_date: DateTime (Invoice creation date)
    - payment_method: Text (Card, Bank Transfer, etc.)
    
    # Relationships:
    - subscription: Many-to-One with Subscription
```

---

### 🛣️ API Routes (`app/routes/`)

#### `user_router.py` - User Management Routes
```python
# Endpoints:
- GET /users/me - Get current user info
- GET /users/me/auth-status - Check authentication status
```

#### `profile_router.py` - Profile Management Routes
```python
# Endpoints:
- GET /profiles/me - Get current user's profile
- POST /profiles/ - Create new profile
- PUT /profiles/me - Update current profile
- DELETE /profiles/me - Delete current profile
- GET /profiles/{user_id} - Get profile by ID (public)
```

#### `supabase_auth_router.py` - Authentication Routes
```python
# Endpoints:
- POST /supabase-auth/signup - User registration
- POST /supabase-auth/signin - User login
- POST /supabase-auth/refresh - Token refresh
- POST /supabase-auth/signout - User logout
- GET /supabase-auth/user - Get user from token
- GET /supabase-auth/debug - Debug configuration
```

#### `subscription_router_new.py` - Subscription Management Routes
```python
# Endpoints:
- GET /subscriptions/status - Get subscription status
- GET /subscriptions/plans - Get available plans
- POST /subscriptions/subscribe - Subscribe to plan
- GET /subscriptions/my-subscriptions - Get user subscriptions
- GET /subscriptions/features/{feature} - Get feature usage
- POST /subscriptions/features/{feature}/use - Use feature
- PUT /subscriptions/extend - Extend subscription
- PUT /subscriptions/cancel - Cancel subscription
- GET /subscriptions/invoices - Get user invoices
- POST /subscriptions/invoices - Create invoice
- GET /subscriptions/usage-tracking - Get usage tracking
- POST /subscriptions/admin/cleanup-expired - Admin cleanup
- GET /subscriptions/admin/usage-stats - Admin statistics
```

#### `premium_router_new.py` - Premium Features Routes
```python
# Endpoints:
- GET /premium/status - Get premium status
- GET /premium/feature-limits - Get feature limits
- POST /premium/check-access - Check feature access
```

---

### 📋 Data Schemas (`app/schemas/`)

#### `profile.py` - Profile Data Schemas
```python
# Schemas:
- AccountTypeEnum: Enum for account types (PERSONAL, BUSINESS)
- ProfileBase: Base profile fields (includes account_type)
- ProfileCreate: Profile creation data
- ProfileUpdate: Profile update data (optional account_type)
- ProfileResponse: Profile response data
- UserAuth: User authentication data
- TokenData: JWT token data
```

**Purpose**: Pydantic models for request/response validation and serialization

---

### 🔧 Business Logic (`app/services/`)

#### `profile_service.py` - Profile Business Logic
```python
class ProfileService:
    # Methods:
    - create_profile(): Create new user profile
    - get_profile_response_by_id(): Get profile by ID
    - update_profile(): Update existing profile
    - delete_profile(): Delete user profile
    - create_profile_if_not_exists(): Auto-create profile
```

#### `subscription_service.py` - Subscription Business Logic
```python
class SubscriptionServiceNew:
    # Methods:
    - get_plans(): Get available subscription plans
    - get_plan(): Get specific plan
    - create_subscription(): Create new subscription
    - get_user_subscriptions(): Get user's subscriptions
    - get_feature_usage(): Get feature usage info
    - increment_feature_usage(): Track feature usage
    - extend_subscription(): Extend subscription
    - cancel_subscription(): Cancel subscription
    - get_user_invoices(): Get user invoices
    - create_invoice(): Create new invoice
    - get_usage_tracking(): Get usage tracking
    - cleanup_expired_subscriptions(): Admin cleanup
```

---

### 🛠️ Utilities (`app/utils/`)

#### `auth.py` - Authentication Utilities
```python
# Functions:
- get_current_user(): Extract user from JWT token
- get_current_user_id(): Get current user ID
- verify_token(): Verify JWT token
- create_access_token(): Create JWT token (for testing)
- decode_token(): Decode JWT token
```

#### `subscription.py` - Subscription Utilities
```python
# Functions:
- get_subscription_status(): Get user's subscription status
- check_feature_access(): Check if user can access feature
- get_usage_info(): Get usage information
```

---

## 🧪 Testing (`tests/`)

### Test Files
- `test_items.py` - Item-related tests
- `test_users.py` - User-related tests
- `__init__.py` - Test package initialization

---

## 📚 Documentation (`docs/`)

### Schema Files
- `database_setup_new.sql` - **Main database schema** (Primary)
- `create_tables_exact.sql` - Alternative schema
- `add_missing_foreign_keys.sql` - Foreign key constraints

### Documentation Files
- `AUTH_SYSTEM.md` - Authentication system documentation
- `ENHANCED_SUBSCRIPTION_SYSTEM.md` - Subscription system docs
- `RELATIONSHIP_BENEFITS.md` - Database relationships documentation

---

## 🔄 Database Migrations (`alembic/`)

### Migration Structure
- `env.py` - Alembic environment configuration
- `script.py.mako` - Migration script template
- `versions/` - Migration version files

### Configuration
- `alembic.ini` - Alembic configuration file

---

## 🚀 Application Flow

### 1. **Startup Process**
```
run.py → app/main.py → Database Connection → Table Creation → Router Registration
```

### 2. **Request Flow**
```
Client Request → CORS Middleware → Router → Service Layer → Database → Response
```

### 3. **Authentication Flow**
```
User Login → Supabase Auth → JWT Token → Token Validation → Protected Routes
```

### 4. **Subscription Flow**
```
User Signup → Profile Creation → Trial Subscription → Plan Selection → Usage Tracking
```

---

## 🔧 Configuration Files

### Environment Configuration (`supabase.env`)
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_JWT_SECRET=your-jwt-secret
DATABASE_URL=postgresql+asyncpg://...
```

### Dependencies (`requirements.txt`)
- FastAPI - Web framework
- SQLAlchemy - ORM
- Supabase - Authentication client
- Alembic - Database migrations
- Pydantic - Data validation
- Uvicorn - ASGI server

---

## 🏃‍♂️ Running the Application

### Development Server
```bash
# Option 1: Using run.py
python run.py

# Option 2: Using start_server.py
python start_server.py

# Option 3: Direct uvicorn
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Access Points
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health
- **Root Info**: http://localhost:8000/

---

## 🔐 Security Features

### Authentication
- Supabase JWT token validation
- Row Level Security (RLS) policies
- Protected route middleware

### Data Protection
- Foreign key constraints
- Input validation with Pydantic
- SQL injection prevention via SQLAlchemy

### CORS Configuration
- Configurable allowed origins
- Credential support
- Multiple HTTP methods

---

## 📊 Key Features

### User Management
- ✅ Supabase authentication integration
- ✅ User profile management
- ✅ JWT token handling

### Subscription System
- ✅ Multiple subscription plans
- ✅ Usage tracking and limits
- ✅ Billing and invoicing
- ✅ Feature access control

### Database Features
- ✅ Async PostgreSQL with Supabase
- ✅ Automatic table creation
- ✅ Migration support with Alembic
- ✅ Relationship management

### API Features
- ✅ RESTful API design
- ✅ Automatic API documentation
- ✅ CORS support
- ✅ Error handling
- ✅ Health checks

---

## 🎯 Architecture Patterns

### **Layered Architecture**
- **Presentation Layer**: FastAPI routes
- **Business Logic Layer**: Services
- **Data Access Layer**: SQLAlchemy models
- **Database Layer**: PostgreSQL/Supabase

### **Dependency Injection**
- Database sessions via FastAPI dependencies
- Authentication via middleware
- Configuration via environment variables

### **Repository Pattern**
- Service classes encapsulate data access
- Models handle database operations
- Schemas handle data validation

---

This application provides a robust, scalable foundation for a subscription-based SaaS platform with comprehensive user management, billing, and feature access control.
