# Email Validation and Duplicate User Handling

## Overview

This document explains the comprehensive email validation system and duplicate user handling implemented in the signup process.

## Email Validation Features

### 1. Comprehensive Email Validation

The system now includes detailed email validation with specific error messages:

#### Validation Rules:
- **Required**: Email cannot be empty
- **Length**: Maximum 254 characters (RFC 5321 limit)
- **Structure**: Must contain exactly one '@' symbol
- **Local Part** (before @):
  - Maximum 64 characters
  - Cannot start or end with dots
  - Cannot contain consecutive dots
  - Only allows: letters, numbers, dots, underscores, plus signs, hyphens
- **Domain Part** (after @):
  - Maximum 253 characters
  - Must contain at least one dot
  - Cannot start or end with dots
  - Cannot contain consecutive dots
  - Only allows: letters, numbers, dots, hyphens
- **TLD**: Must be at least 2 characters

#### Error Messages:
- `"Email address is required"`
- `"Email address cannot be empty"`
- `"Email address is too long (maximum 254 characters)"`
- `"Email address must contain '@' symbol"`
- `"Email address must contain exactly one '@' symbol"`
- `"Email address must have a local part before '@'"`
- `"Local part of email is too long (maximum 64 characters)"`
- `"Local part of email cannot start or end with a dot"`
- `"Local part of email cannot contain consecutive dots"`
- `"Email address must have a domain part after '@'"`
- `"Domain part is too long (maximum 253 characters)"`
- `"Domain part must contain at least one dot"`
- `"Domain part cannot start or end with a dot"`
- `"Domain part cannot contain consecutive dots"`
- `"Local part contains invalid characters. Only letters, numbers, dots, underscores, plus signs, and hyphens are allowed"`
- `"Domain part contains invalid characters. Only letters, numbers, dots, and hyphens are allowed"`
- `"Domain must have a valid top-level domain (at least 2 characters)"`
- `"Email address format is invalid"`

### 2. Pre-Supabase Validation

Before sending the request to Supabase, the system performs additional validation:

```python
# Pre-validate email format before sending to Supabase
if not re.match(r'^[a-zA-Z0-9._+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', signup_data.email):
    validation_results["user_creation"]["error"] = "Email format is invalid"
    raise HTTPException(status_code=400, detail="Email format is invalid")
```

## Duplicate User Handling

### 1. Database-Level Check

The system checks if a profile already exists for the user ID returned by Supabase:

```python
# Check if user already exists by checking if profile exists in our database
from ..services.profile_service import ProfileService
profile_service = ProfileService(db)
existing_profile = await profile_service.get_profile_by_id(user_id)

if existing_profile:
    validation_results["user_creation"]["error"] = "User with this email already exists"
    raise HTTPException(
        status_code=409, 
        detail={
            "message": "User already exists",
            "error": f"A user with email '{signup_data.email}' already exists. Please use a different email or try signing in instead.",
            "email": signup_data.email,
            "user_exists": True,
            "validation_results": validation_results
        }
    )
```

### 2. Supabase Error Handling

The system also handles Supabase-specific duplicate user errors:

```python
elif e.status_code == 422 and "already registered" in str(e.detail).lower():
    # Handle user already exists error from Supabase
    validation_results["user_creation"]["error"] = "User with this email already exists"
    raise HTTPException(
        status_code=409, 
        detail={
            "message": "User already exists",
            "error": f"A user with email '{signup_data.email}' already exists. Please use a different email or try signing in instead.",
            "email": signup_data.email,
            "user_exists": True,
            "validation_results": validation_results
        }
    )
```

## Response Format

### Successful Signup Response:
```json
{
  "message": "User and profile created successfully",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "profile": {
    "id": "uuid",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "0509556183",
    "account_type": "personal",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "profile_created": true,
  "profile_message": "Profile created successfully",
  "validation_results": {
    "user_creation": {
      "success": true,
      "error": null,
      "data": {...}
    },
    "profile_creation": {
      "success": true,
      "error": null,
      "data": {...}
    },
    "overall_success": true
  }
}
```

### Duplicate User Error Response:
```json
{
  "message": "User already exists",
  "error": "A user with email 'user@example.com' already exists. Please use a different email or try signing in instead.",
  "email": "user@example.com",
  "user_exists": true,
  "validation_results": {
    "user_creation": {
      "success": false,
      "error": "User with this email already exists",
      "data": null
    },
    "profile_creation": {
      "success": false,
      "error": null,
      "data": null
    },
    "overall_success": false
  }
}
```

### Email Validation Error Response:
```json
{
  "message": "Email validation failed",
  "error": "The email address format is valid but not accepted by the authentication service. Please try a different email address.",
  "email": "user@example.com",
  "validation_results": {
    "user_creation": {
      "success": false,
      "error": "Email address is invalid or not accepted by the authentication service",
      "data": null
    },
    "profile_creation": {
      "success": false,
      "error": null,
      "data": null
    },
    "overall_success": false
  }
}
```

## Testing

### Valid Email Examples:
- `user@example.com`
- `test.user+tag@domain.co.uk`
- `user123@subdomain.example.org`

### Invalid Email Examples:
- `invalid-email` → "Email address must contain '@' symbol"
- `@gmail.com` → "Email address must have a local part before '@'"
- `user@` → "Email address must have a domain part after '@'"
- `user..test@gmail.com` → "Local part of email cannot contain consecutive dots"
- `.user@gmail.com` → "Local part of email cannot start or end with a dot"
- `user@gmail..com` → "Domain part cannot contain consecutive dots"

### Duplicate User Testing:
1. Sign up with a new email → Should succeed
2. Try to sign up again with the same email → Should return "User already exists" error

## Configuration Notes

### Supabase Email Validation Issue

If Supabase is rejecting valid emails with "email_address_invalid" error, this might be due to:

1. **Supabase Project Configuration**: Check Supabase dashboard settings
2. **Email Domain Restrictions**: Some Supabase projects have domain restrictions
3. **Email Provider Settings**: Check if email providers are properly configured

### Troubleshooting

1. **Check Supabase Dashboard**: Go to Authentication > Settings > Email Templates
2. **Verify Email Configuration**: Ensure SMTP settings are correct
3. **Check Domain Restrictions**: Look for any domain allowlists/blocklists
4. **Test with Different Domains**: Try emails from different providers (gmail, yahoo, etc.)

## Implementation Files

- `app/routes/supabase_auth_router.py` - Main signup endpoint with validation
- `app/utils/signup_validation.py` - Comprehensive validation utilities
- `app/services/profile_service.py` - Profile existence checking
- `docs/EMAIL_VALIDATION_AND_DUPLICATE_USER_HANDLING.md` - This documentation

## Status Codes

- `200` - Successful signup
- `400` - Email validation failed
- `409` - User already exists
- `422` - Supabase validation error
- `500` - Internal server error
