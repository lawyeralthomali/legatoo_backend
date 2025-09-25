# API Documentation

## Base URL
```
http://localhost:8000
```

## Authentication
All protected endpoints require a Bearer token in the Authorization header:
```
Authorization: Bearer <your_jwt_token>
```

---

## 🔐 Authentication Endpoints (`/supabase-auth`)

### Sign Up
**POST** `/supabase-auth/signup`

Create a new user account with Supabase Auth.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123",
  "full_name": "John Doe"  // optional
}
```

**Response:**
```json
{
  "message": "User created successfully",
  "user": { ... },
  "session": { ... },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_at": 1234567890
}
```

### Sign In
**POST** `/supabase-auth/signin`

Authenticate user and get JWT token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "message": "Sign in successful",
  "user": { ... },
  "session": { ... },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_at": 1234567890
}
```

### Refresh Token
**POST** `/supabase-auth/refresh`

Refresh an expired JWT token.

**Request Body:**
```json
{
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Sign Out
**POST** `/supabase-auth/signout`

Sign out user and invalidate token.

**Request Body:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### Get User Info
**GET** `/supabase-auth/user`
*Requires Authentication*

Get current user information from JWT token.

**Response:**
```json
{
  "user_id": "uuid-string",
  "email": "user@example.com",
  "phone": "+1234567890",
  "aud": "authenticated",
  "role": "authenticated",
  "iat": 1234567890,
  "exp": 1234567890,
  "iss": "supabase-url"
}
```

### Debug Configuration
**GET** `/supabase-auth/debug`

Debug Supabase configuration and test connection.

---

## 👤 User Endpoints (`/users`)

### Get Current User
**GET** `/users/me`
*Requires Authentication*

Get current authenticated user's information.

**Response:**
```json
{
  "id": "uuid-string",
  "email": "user@example.com",
  "phone": "+1234567890",
  "aud": "authenticated",
  "role": "authenticated",
  "created_at": "1234567890",
  "updated_at": "1234567890"
}
```

### Check Auth Status
**GET** `/users/me/auth-status`
*Requires Authentication*

Check if user is authenticated and return basic auth status.

**Response:**
```json
{
  "authenticated": true,
  "user_id": "uuid-string",
  "email": "user@example.com",
  "phone": "+1234567890",
  "role": "authenticated"
}
```

---

## 👤 Profile Endpoints (`/profiles`)

### Get My Profile
**GET** `/profiles/me`
*Requires Authentication*

Get current user's profile. Creates a profile if it doesn't exist.

**Response:**
```json
{
  "id": "uuid-string",
  "full_name": "John Doe",
  "avatar_url": "https://example.com/avatar.jpg",
  "bio": "Software Developer",
  "account_type": "personal",
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### Create Profile
**POST** `/profiles/`
*Requires Authentication*

Create a new profile for the current user.

**Request Body:**
```json
{
  "full_name": "John Doe",
  "avatar_url": "https://example.com/avatar.jpg",
  "bio": "Software Developer",
  "account_type": "personal"
}
```

### Update Profile
**PUT** `/profiles/me`
*Requires Authentication*

Update current user's profile.

**Request Body:**
```json
{
  "full_name": "John Doe Updated",
  "avatar_url": "https://example.com/new-avatar.jpg",
  "bio": "Senior Software Developer"
}
```

### Delete Profile
**DELETE** `/profiles/me`
*Requires Authentication*

Delete current user's profile.

### Get Profile by ID
**GET** `/profiles/{user_id}`

Get a profile by user ID (public endpoint).

---

## 💳 Subscription Endpoints (`/subscriptions`)

### Get Subscription Status
**GET** `/subscriptions/status`
*Requires Authentication*

Get current user's subscription status and usage information.

**Response:**
```json
{
  "has_active_subscription": true,
  "subscription": {
    "subscription_id": "uuid-string",
    "plan_name": "Basic Monthly",
    "plan_type": "monthly",
    "price": 29.99,
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-02-01T00:00:00Z",
    "status": "active",
    "days_remaining": 15
  },
  "usage": {
    "file_upload": {"used": 5, "limit": 50},
    "ai_chat": {"used": 10, "limit": 100},
    "contract": {"used": 2, "limit": 10},
    "report": {"used": 1, "limit": 5},
    "token": {"used": 1000, "limit": 10000},
    "multi_user": {"used": 1, "limit": 3}
  }
}
```

### Get Available Plans
**GET** `/subscriptions/plans`

Get all available subscription plans.

**Query Parameters:**
- `active_only` (boolean, default: true) - Show only active plans

**Response:**
```json
[
  {
    "plan_id": "uuid-string",
    "plan_name": "Free Trial",
    "plan_type": "free",
    "price": 0,
    "billing_cycle": "none",
    "file_limit": 5,
    "ai_message_limit": 10,
    "contract_limit": 2,
    "report_limit": 1,
    "token_limit": 1000,
    "multi_user_limit": 1,
    "government_integration": false,
    "description": "7-day free trial with limited features",
    "is_active": true
  }
]
```

### Subscribe to Plan
**POST** `/subscriptions/subscribe`
*Requires Authentication*

Subscribe to a plan.

**Request Body:**
```json
{
  "plan_id": "uuid-string",
  "duration_days": 30  // optional, defaults to plan's billing cycle
}
```

**Response:**
```json
{
  "subscription_id": "uuid-string",
  "plan_name": "Basic Monthly",
  "plan_type": "monthly",
  "price": 29.99,
  "billing_cycle": "monthly",
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-02-01T00:00:00Z",
  "status": "active"
}
```

### Get My Subscriptions
**GET** `/subscriptions/my-subscriptions`
*Requires Authentication*

Get current user's all subscriptions.

**Response:**
```json
[
  {
    "subscription_id": "uuid-string",
    "plan_name": "Basic Monthly",
    "plan_type": "monthly",
    "price": 29.99,
    "billing_cycle": "monthly",
    "start_date": "2024-01-01T00:00:00Z",
    "end_date": "2024-02-01T00:00:00Z",
    "status": "active",
    "is_active": true,
    "days_remaining": 15,
    "current_usage": {
      "file_upload": 5,
      "ai_chat": 10,
      "contract": 2
    }
  }
]
```

### Get Feature Usage
**GET** `/subscriptions/features/{feature}`
*Requires Authentication*

Get feature usage information for a specific feature.

**Path Parameters:**
- `feature` - Feature name (file_upload, ai_chat, contract, report, token, multi_user)

**Response:**
```json
{
  "feature": "file_upload",
  "used": 5,
  "limit": 50,
  "remaining": 45,
  "can_use": true
}
```

### Use Feature
**POST** `/subscriptions/features/{feature}/use`
*Requires Authentication*

Use a feature (increment usage).

**Path Parameters:**
- `feature` - Feature name

**Request Body:**
```json
{
  "amount": 1  // optional, defaults to 1
}
```

**Response:**
```json
{
  "message": "Successfully used 1 file_upload(s)"
}
```

### Extend Subscription
**PUT** `/subscriptions/extend`
*Requires Authentication*

Extend current subscription.

**Request Body:**
```json
{
  "days": 30
}
```

**Response:**
```json
{
  "message": "Subscription extended by 30 days",
  "new_end_date": "2024-03-01T00:00:00Z",
  "days_remaining": 45
}
```

### Cancel Subscription
**PUT** `/subscriptions/cancel`
*Requires Authentication*

Cancel current subscription.

**Response:**
```json
{
  "message": "Subscription cancelled successfully"
}
```

### Get My Invoices
**GET** `/subscriptions/invoices`
*Requires Authentication*

Get current user's invoices.

**Response:**
```json
[
  {
    "invoice_id": "uuid-string",
    "amount": 29.99,
    "currency": "SAR",
    "status": "paid",
    "invoice_date": "2024-01-01T00:00:00Z",
    "payment_method": "Card"
  }
]
```

### Create Invoice
**POST** `/subscriptions/invoices`
*Requires Authentication*

Create a new invoice.

**Request Body:**
```json
{
  "subscription_id": "uuid-string",
  "amount": 29.99,
  "currency": "SAR",  // optional, defaults to "SAR"
  "payment_method": "Card"  // optional
}
```

### Get Usage Tracking
**GET** `/subscriptions/usage-tracking`
*Requires Authentication*

Get usage tracking information.

**Response:**
```json
[
  {
    "usage_id": "uuid-string",
    "feature": "file_upload",
    "used_count": 5,
    "reset_cycle": "monthly",
    "last_reset": "2024-01-01T00:00:00Z"
  }
]
```

---

## 🔧 Admin Endpoints

### Cleanup Expired Subscriptions
**POST** `/subscriptions/admin/cleanup-expired`

Clean up expired subscriptions (admin endpoint).

**Response:**
```json
{
  "message": "Cleaned up 5 expired subscriptions"
}
```

### Get Usage Statistics
**GET** `/subscriptions/admin/usage-stats`

Get usage statistics (admin endpoint).

---

## Error Responses

All endpoints may return the following error responses:

### 400 Bad Request
```json
{
  "detail": "Invalid request data"
}
```

### 401 Unauthorized
```json
{
  "detail": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```

### 404 Not Found
```json
{
  "detail": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "detail": "Internal server error"
}
```

---

## Example Usage

### 1. Sign Up and Get Token
```bash
curl -X POST "http://localhost:8000/supabase-auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "password": "password123",
    "full_name": "John Doe"
  }'
```

### 2. Use Token for Authenticated Requests
```bash
curl -X GET "http://localhost:8000/subscriptions/status" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### 3. Subscribe to a Plan
```bash
curl -X POST "http://localhost:8000/subscriptions/subscribe" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "plan_id": "PLAN_UUID_HERE"
  }'
```

### 4. Use a Feature
```bash
curl -X POST "http://localhost:8000/subscriptions/features/file_upload/use" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "amount": 1
  }'
```

---

## Notes

- All timestamps are in ISO 8601 format
- UUIDs are used for all IDs
- Currency is in SAR (Saudi Riyal) by default
- All monetary values are in decimal format
- Feature limits are enforced automatically
- Subscriptions automatically expire based on end_date
- Usage tracking resets based on billing cycle

