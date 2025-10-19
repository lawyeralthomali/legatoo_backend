# Signup with Automatic Profile Creation

## Overview
The signup endpoint now automatically creates a user profile when a new user registers. This ensures every user has a profile immediately after signup.

## API Endpoint
```
POST /supabase-auth/signup
```

## Request Body
```json
{
  "email": "user@example.com",
  "password": "securepassword123",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "+1234567890"
}
```

## Response (Success)
```json
{
  "message": "User created successfully",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "profile": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+1234567890",
    "account_type": "personal"
  },
  "session": {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "expires_at": 1640995200
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "expires_at": 1640995200
}
```

## Response (Profile Creation Failed)
```json
{
  "message": "User created successfully, but profile creation failed",
  "user": {
    "id": "123e4567-e89b-12d3-a456-426614174000",
    "email": "user@example.com"
  },
  "profile": null,
  "session": { ... },
  "access_token": "...",
  "refresh_token": "...",
  "expires_at": 1640995200,
  "warning": "Profile creation failed - user can create profile later"
}
```

## Field Requirements

### Required Fields
- `email`: Valid email address
- `password`: User password

### Optional Fields
- `first_name`: User's first name (defaults to "User")
- `last_name`: User's last name (defaults to "User")
- `phone_number`: User's phone number (max 20 characters)

## Default Values
- `first_name`: "User" (if not provided)
- `last_name`: "User" (if not provided)
- `phone_number`: null (if not provided)
- `account_type`: "personal"
- `avatar_url`: null

## Error Handling
- If Supabase user creation fails, the entire request fails
- If profile creation fails, user is still created but profile is null
- User can create profile later using the profile endpoints

## Example Usage

### cURL
```bash
curl -X POST "http://localhost:8000/supabase-auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "john.doe@example.com",
    "password": "securepassword123",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+1234567890"
  }'
```

### JavaScript/Fetch
```javascript
const response = await fetch('/supabase-auth/signup', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email: 'john.doe@example.com',
    password: 'securepassword123',
    first_name: 'John',
    last_name: 'Doe',
    phone_number: '+1234567890'
  })
});

const data = await response.json();
console.log('User created:', data.user);
console.log('Profile created:', data.profile);
```

### Python/Requests
```python
import requests

response = requests.post('http://localhost:8000/supabase-auth/signup', json={
    'email': 'john.doe@example.com',
    'password': 'securepassword123',
    'first_name': 'John',
    'last_name': 'Doe',
    'phone_number': '+1234567890'
})

data = response.json()
print('User created:', data['user'])
print('Profile created:', data['profile'])
```

## Benefits
1. **Automatic Profile Creation**: No need for separate profile creation step
2. **Consistent Data**: Every user has a profile immediately
3. **Better UX**: Users don't need to complete profile setup later
4. **Error Resilience**: User creation succeeds even if profile creation fails
5. **Structured Data**: Uses Pydantic models for validation
