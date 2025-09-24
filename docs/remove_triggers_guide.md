# Remove Database Triggers Guide

## Overview
This guide will help you remove all database triggers and functions related to automatic profile creation so you can test the backend-only approach.

## Step-by-Step Process

### Step 1: Check What Currently Exists
First, run this script to see what triggers and functions are currently in your database:

```sql
-- Run in Supabase SQL Editor
\i docs/check_existing_triggers.sql
```

This will show you:
- All existing triggers
- All existing functions
- Specifically user and profile related triggers/functions

### Step 2: Remove Triggers and Functions
Run the cleanup script to remove all automatic profile creation logic:

```sql
-- Run in Supabase SQL Editor
\i docs/cleanup_automatic_profile_creation.sql
```

This will:
- ✅ Remove all user creation triggers
- ✅ Remove all automatic profile creation functions
- ✅ Keep the profiles table structure intact
- ✅ Keep the updated_at trigger (optional)

### Step 3: Verify Cleanup
After running the cleanup, verify that triggers are removed:

```sql
-- Check remaining triggers
SELECT trigger_name, event_object_table, trigger_schema
FROM information_schema.triggers 
WHERE trigger_schema IN ('public', 'auth');

-- Check remaining functions
SELECT routine_name, routine_type
FROM information_schema.routines 
WHERE routine_schema = 'public';
```

### Step 4: Test Backend Profile Creation
Now you can test the backend-only profile creation:

1. **Sign up a new user** using the `/supabase-auth/signup` endpoint
2. **Check the response** - it should include profile creation status
3. **Verify in database** - check that profile was created in the `profiles` table

## What Gets Removed

### Triggers Removed:
- `on_auth_user_created` - Trigger on auth.users table
- `handle_new_user_trigger` - Any custom user creation trigger
- `auth_user_created` - Alternative trigger name

### Functions Removed:
- `handle_new_user()` - Function that creates profiles automatically
- `create_user_profile()` - Alternative profile creation function
- `on_auth_user_created()` - Alternative function name

### What Stays:
- ✅ `profiles` table structure
- ✅ All profile columns (`first_name`, `last_name`, `phone_number`, etc.)
- ✅ Constraints and indexes
- ✅ `updated_at` trigger (optional)

## Testing the Backend Approach

### 1. Test Signup with Profile Creation
```bash
curl -X POST "http://localhost:8000/supabase-auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "password": "password123",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+1234567890"
  }'
```

Expected response:
```json
{
  "message": "User created successfully",
  "user": { "id": "uuid", "email": "test@example.com" },
  "profile": {
    "id": "uuid",
    "first_name": "John",
    "last_name": "Doe",
    "phone_number": "+1234567890",
    "account_type": "personal"
  },
  "profile_created": true,
  "profile_message": "Profile created successfully",
  "session": { ... }
}
```

### 2. Test Profile Creation Utility
```python
from app.utils.profile_creation import ensure_user_profile

# In any endpoint
profile_result = await ensure_user_profile(
    db=db,
    user_id=user_id,
    first_name="Jane",
    last_name="Smith"
)

print(f"Profile created: {profile_result['created']}")
print(f"Message: {profile_result['message']}")
```

### 3. Verify Database
Check that profiles are created in the database:

```sql
-- Check profiles table
SELECT 
    id,
    first_name,
    last_name,
    phone_number,
    account_type,
    created_at
FROM public.profiles
ORDER BY created_at DESC;
```

## Troubleshooting

### If Triggers Still Exist:
1. Check the exact trigger names in your database
2. Manually drop them:
   ```sql
   DROP TRIGGER IF EXISTS [trigger_name] ON [table_name];
   ```

### If Functions Still Exist:
1. Check the exact function names:
   ```sql
   SELECT routine_name FROM information_schema.routines 
   WHERE routine_schema = 'public';
   ```
2. Manually drop them:
   ```sql
   DROP FUNCTION IF EXISTS [function_name]();
   ```

### If Profile Creation Fails:
1. Check the backend logs for errors
2. Verify the profiles table structure
3. Check that the ProfileService is working correctly

## Benefits After Cleanup

1. **Full Control** - Profile creation is handled entirely by your backend code
2. **Better Error Handling** - You can catch and handle profile creation errors
3. **Easier Testing** - You can mock profile creation in tests
4. **Better Logging** - You can log profile creation events
5. **Flexibility** - You can customize profile creation per endpoint

## Rollback (If Needed)

If you need to restore the triggers later, you can run the original migration script:

```sql
-- Restore triggers (if needed)
\i docs/update_profiles_table.sql
```

But remember to remove them again if you want to use the backend-only approach.
