# Production Authentication Configuration Update

## 🌐 Updated Backend URL
**New Production Backend URL:** `http://srv1022733.hstgr.cloud:8000`

## 🔐 Authentication Endpoints

### Login Endpoint
```
POST http://srv1022733.hstgr.cloud:8000/api/v1/auth/login
```

**Request Body:**
```json
{
  "email": "info@legatoo.westlinktowing.com",
  "password": "Zaq1zaq1"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Login successful",
  "data": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": 1,
      "email": "info@legatoo.westlinktowing.com",
      "role": "super_admin",
      "is_active": true,
      "is_verified": true
    }
  },
  "errors": []
}
```

### Signup Endpoint
```
POST http://srv1022733.hstgr.cloud:8000/api/v1/auth/signup
```

### Refresh Token Endpoint
```
POST http://srv1022733.hstgr.cloud:8000/api/v1/auth/refresh-token
```

### Logout Endpoint
```
POST http://srv1022733.hstgr.cloud:8000/api/v1/auth/logout
```

## 🔒 Protected Routes (Now Require Authentication)

All the following routes now require a valid JWT token in the Authorization header:

### User Management
- `GET /api/v1/users/` - Get all users
- `GET /api/v1/users/{user_id}` - Get specific user
- `GET /api/v1/users/search` - Search users
- `GET /api/v1/users/{user_id}/profile` - Get user profile
- `GET /api/v1/users/{user_id}/complete` - Get user with profile

### Contract Templates
- `GET /api/contracts/templates/` - Get templates
- `GET /api/contracts/templates/{template_id}` - Get specific template
- `POST /api/contracts/templates/` - Create template
- `PUT /api/contracts/templates/{template_id}` - Update template
- `DELETE /api/contracts/templates/{template_id}` - Delete template
- `POST /api/contracts/templates/{template_id}/generate` - Generate contract

### Contract Categories
- `GET /api/contracts/categories/` - Get categories
- `GET /api/contracts/categories/{category_id}` - Get specific category
- `POST /api/contracts/categories/` - Create category
- `PUT /api/contracts/categories/{category_id}` - Update category
- `DELETE /api/contracts/categories/{category_id}` - Delete category

### Legal Assistant
- `POST /api/v1/legal-assistant/chat` - AI chat (requires auth)
- `GET /api/v1/legal-assistant/status` - Status check (public)
- `POST /api/v1/legal-assistant/detect-language` - Language detection (public)

## 🛡️ Security Headers

When making authenticated requests, include the JWT token in the Authorization header:

```javascript
const headers = {
  'Authorization': `Bearer ${access_token}`,
  'Content-Type': 'application/json'
};
```

## 📱 Frontend Configuration

Use the `frontend-config.js` file for frontend applications:

```javascript
import config from './frontend-config.js';

// Login request
const loginResponse = await fetch(config.AUTH_ENDPOINTS.LOGIN, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json'
  },
  body: JSON.stringify({
    email: 'info@legatoo.westlinktowing.com',
    password: 'Zaq1zaq1'
  })
});
```

## 🚀 Deployment

Use the updated deployment script:

```bash
chmod +x deploy_production_updated.sh
./deploy_production_updated.sh
```

## ✅ Security Improvements

1. **All sensitive routes now require authentication**
2. **JWT tokens are required for user data access**
3. **CORS is properly configured for production**
4. **Environment variables are set for production**
5. **Debug mode is disabled in production**

## 🔍 Testing Authentication

Test the authentication with curl:

```bash
# Login
curl -X POST "http://srv1022733.hstgr.cloud:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email": "info@legatoo.westlinktowing.com", "password": "Zaq1zaq1"}'

# Test protected route (should fail without token)
curl "http://srv1022733.hstgr.cloud:8000/api/v1/users/"

# Test protected route with token (should succeed)
curl "http://srv1022733.hstgr.cloud:8000/api/v1/users/" \
  -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

The backend is now properly secured and configured for production use at `http://srv1022733.hstgr.cloud:8000`!
