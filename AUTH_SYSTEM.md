# Production-Ready Authentication System

This is a complete, production-ready authentication system built with FastAPI, SQLAlchemy, and JWT tokens.

## 🏗️ Architecture

### **Modular Structure**
```
app/
├── models/user.py          # SQLAlchemy User model
├── schemas/user.py         # Pydantic schemas for validation
├── services/user_service.py # Business logic layer
├── routes/user_router.py   # API endpoints
├── utils/
│   ├── jwt.py             # JWT token management
│   └── hashing.py         # Password hashing utilities
└── db/database.py         # Database configuration
```

## 🔐 Features

### **User Management**
- ✅ User registration with email/username validation
- ✅ Secure password hashing with bcrypt
- ✅ User profile management
- ✅ Account activation/deactivation

### **JWT Authentication**
- ✅ Access tokens (30 minutes expiry)
- ✅ Refresh tokens (7 days expiry)
- ✅ Token blacklisting for logout
- ✅ Automatic token refresh

### **Security Features**
- ✅ Password strength validation
- ✅ Duplicate email/username prevention
- ✅ Secure password reset flow
- ✅ Token-based authentication
- ✅ CORS middleware configured

## 🚀 API Endpoints

### **Authentication**
- `POST /api/v1/users/register` - Register new user
- `POST /api/v1/users/login` - Login with username/email + password
- `POST /api/v1/users/refresh` - Get new access token using refresh token
- `POST /api/v1/users/logout` - Logout (revoke access token)
- `POST /api/v1/users/logout-all` - Logout from all sessions

### **User Profile**
- `GET /api/v1/users/me` - Get current user profile
- `PUT /api/v1/users/me` - Update user profile
- `POST /api/v1/users/change-password` - Change password

### **Password Reset**
- `POST /api/v1/users/request-password-reset` - Request password reset
- `POST /api/v1/users/reset-password` - Reset password with code

## 📊 Database Schema

### **Users Table**
```sql
CREATE TABLE users (
    id INTEGER PRIMARY KEY,
    email VARCHAR UNIQUE NOT NULL,
    username VARCHAR UNIQUE NOT NULL,
    hashed_password VARCHAR NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME
);
```

## 🔧 Configuration

### **Environment Variables**
```bash
SECRET_KEY=your-secret-key-change-in-production
DATABASE_URL=sqlite+aiosqlite:///./test.db  # For testing
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost/db  # For production
```

### **JWT Settings**
- Access Token: 30 minutes
- Refresh Token: 7 days
- Algorithm: HS256

## 🧪 Testing the API

### **1. Register a User**
```bash
curl -X POST "http://localhost:8000/api/v1/users/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "securepassword123"
  }'
```

### **2. Login**
```bash
curl -X POST "http://localhost:8000/api/v1/users/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username_or_email": "testuser",
    "password": "securepassword123"
  }'
```

### **3. Access Protected Endpoint**
```bash
curl -X GET "http://localhost:8000/api/v1/users/me" \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN"
```

## 🛡️ Security Best Practices

1. **Change SECRET_KEY** in production
2. **Use HTTPS** in production
3. **Set proper CORS origins**
4. **Use strong passwords**
5. **Implement rate limiting**
6. **Add email verification**
7. **Use Redis for token blacklist** in production

## 🚀 Production Deployment

1. **Database**: Switch to PostgreSQL
2. **Token Storage**: Use Redis for blacklist
3. **Email Service**: Implement real email sending
4. **Environment**: Set production environment variables
5. **SSL**: Enable HTTPS
6. **Monitoring**: Add logging and monitoring

## 📝 Next Steps

This authentication system is ready for:
- ✅ User registration and login
- ✅ JWT-based authentication
- ✅ Password management
- ✅ Profile management

**Future enhancements:**
- 🔄 Email verification
- 🔄 Two-factor authentication
- 🔄 OAuth integration
- 🔄 Subscription management
- 🔄 Role-based access control
