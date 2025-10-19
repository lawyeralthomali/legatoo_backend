# Signup Field Validation Examples

## Overview
The signup endpoint now includes comprehensive field validation to ensure data integrity and security.

## Validation Rules

### 1. Email Validation
- ✅ Must be a valid email format
- ✅ Cannot be a disposable email address
- ✅ Uses EmailStr from Pydantic

**Valid Examples:**
```json
{
  "email": "user@example.com",
  "email": "john.doe@company.org",
  "email": "test+tag@gmail.com"
}
```

**Invalid Examples:**
```json
{
  "email": "invalid-email",
  "email": "user@tempmail.org",  // Disposable email
  "email": "user@10minutemail.com"  // Disposable email
}
```

### 2. Password Validation
- ✅ Minimum 8 characters, maximum 128 characters
- ✅ Must contain at least one uppercase letter
- ✅ Must contain at least one lowercase letter
- ✅ Must contain at least one digit
- ✅ Must contain at least one special character

**Valid Examples:**
```json
{
  "password": "SecurePass123!",
  "password": "MyP@ssw0rd",
  "password": "StrongP@ss1"
}
```

**Invalid Examples:**
```json
{
  "password": "weak",  // Too short
  "password": "password",  // No uppercase, digit, or special char
  "password": "PASSWORD123",  // No lowercase or special char
  "password": "password123",  // No uppercase or special char
  "password": "Password"  // No digit or special char
}
```

### 3. First Name Validation
- ✅ Optional field
- ✅ If provided: 1-100 characters
- ✅ Only letters, spaces, hyphens, and apostrophes
- ✅ No consecutive special characters
- ✅ Automatically trims whitespace

**Valid Examples:**
```json
{
  "first_name": "John",
  "first_name": "Mary-Jane",
  "first_name": "O'Connor",
  "first_name": "Jean Paul"
}
```

**Invalid Examples:**
```json
{
  "first_name": "",  // Empty after trimming
  "first_name": "John123",  // Contains numbers
  "first_name": "John@Doe",  // Contains special chars
  "first_name": "John--Doe",  // Consecutive hyphens
  "first_name": "John  Doe"  // Consecutive spaces
}
```

### 4. Last Name Validation
- ✅ Same rules as first name
- ✅ Optional field
- ✅ If provided: 1-100 characters

**Valid Examples:**
```json
{
  "last_name": "Smith",
  "last_name": "O'Brien",
  "last_name": "Van Der Berg",
  "last_name": "García-López"
}
```

### 5. Phone Number Validation (Saudi Mobile Numbers)
- ✅ Optional field
- ✅ If provided: Must be exactly 10 digits
- ✅ Must start with "05" (Saudi mobile number format)
- ✅ Pattern: 05xxxxxxxx (05 followed by 8 digits)

**Valid Examples:**
```json
{
  "phone_number": "0501234567",
  "phone_number": "0512345678",
  "phone_number": "0523456789",
  "phone_number": "0534567890",
  "phone_number": "0545678901"
}
```

**Invalid Examples:**
```json
{
  "phone_number": "123456789",  // Too short (9 digits)
  "phone_number": "12345678901",  // Too long (11 digits)
  "phone_number": "0401234567",  // Doesn't start with 05
  "phone_number": "0601234567",  // Doesn't start with 05
  "phone_number": "abc123def",  // Contains letters
  "phone_number": "0123456789"  // Starts with 01 instead of 05
}
```

## Complete Request Examples

### Valid Signup Request
```json
{
  "email": "john.doe@example.com",
  "password": "SecurePass123!",
  "first_name": "John",
  "last_name": "Doe",
  "phone_number": "0501234567"
}
```

### Minimal Valid Request
```json
{
  "email": "user@example.com",
  "password": "MyP@ssw0rd",
  "first_name": "User"
}
```

### Invalid Request Examples

#### Weak Password
```json
{
  "email": "user@example.com",
  "password": "weak",
  "first_name": "User"
}
```
**Error Response:**
```json
{
  "detail": [
    {
      "loc": ["body", "password"],
      "msg": "Password must be at least 8 characters long",
      "type": "value_error"
    }
  ]
}
```

#### Invalid Email
```json
{
  "email": "user@tempmail.org",
  "password": "SecurePass123!",
  "first_name": "User"
}
```
**Error Response:**
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "Disposable email addresses are not allowed",
      "type": "value_error"
    }
  ]
}
```

#### Invalid Name
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!",
  "first_name": "John123"
}
```
**Error Response:**
```json
{
  "detail": [
    {
      "loc": ["body", "first_name"],
      "msg": "First name can only contain letters, spaces, hyphens, and apostrophes",
      "type": "value_error"
    }
  ]
}
```

#### Missing Required Fields
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```
**Error Response:**
```json
{
  "detail": "At least first name or last name must be provided for profile creation"
}
```

## Testing the Validation

### Using cURL
```bash
# Valid request
curl -X POST "http://localhost:8000/supabase-auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "SecurePass123!",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+1234567890"
  }'

# Invalid request (weak password)
curl -X POST "http://localhost:8000/supabase-auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "weak",
    "first_name": "John"
  }'
```

### Using Python/Requests
```python
import requests

# Valid request
response = requests.post('http://localhost:8000/supabase-auth/signup', json={
    'email': 'test@example.com',
    'password': 'SecurePass123!',
    'first_name': 'John',
    'last_name': 'Doe',
    'phone_number': '+1234567890'
})

print(f"Status: {response.status_code}")
print(f"Response: {response.json()}")

# Invalid request
response = requests.post('http://localhost:8000/supabase-auth/signup', json={
    'email': 'test@example.com',
    'password': 'weak',
    'first_name': 'John'
})

print(f"Status: {response.status_code}")
print(f"Error: {response.json()}")
```

## Benefits of Validation

1. **Data Integrity** - Ensures all data meets quality standards
2. **Security** - Prevents weak passwords and disposable emails
3. **User Experience** - Clear error messages help users fix issues
4. **API Documentation** - Automatic OpenAPI documentation with validation rules
5. **Consistency** - Standardized data format across the application

## Error Response Format

All validation errors follow the standard FastAPI format:

```json
{
  "detail": [
    {
      "loc": ["body", "field_name"],
      "msg": "Error message",
      "type": "value_error"
    }
  ]
}
```

This makes it easy for frontend applications to parse and display validation errors to users.
