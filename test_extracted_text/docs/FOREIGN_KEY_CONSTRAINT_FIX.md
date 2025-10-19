# Foreign Key Constraint Fix - Database Schema Issue

## ✅ **Issue Identified**

The signup process is failing with a foreign key constraint violation:

```
insert or update on table "profiles" violates foreign key constraint "profiles_id_fkey"
DETAIL: Key (id)=(84d0c089-60dd-4e08-80f0-0daf3ce6a63e) is not present in table "users".
```

### **🔍 Root Cause:**
The `profiles` table has a foreign key constraint `profiles_id_fkey` that references a local `users` table, but:
1. We're using Supabase for user authentication
2. The local `users` table doesn't exist
3. User data is stored in Supabase's `auth.users` table, not locally

## 🔧 **Solution Required**

### **Step 1: Remove Foreign Key Constraint**
Execute this SQL command in your database:

```sql
ALTER TABLE profiles DROP CONSTRAINT IF EXISTS profiles_id_fkey;
```

### **Step 2: Verify Table Structure**
The `profiles` table should have:
- `id` as UUID primary key (corresponds to Supabase `auth.users.id`)
- No foreign key constraints to local tables
- All other profile fields (first_name, last_name, etc.)

## 📋 **Current Error Response**

With the current database constraint, you get:
```json
{
  "success": false,
  "message": "Profile creation failed",
  "data": null,
  "errors": [
    {
      "field": "profile",
      "message": "Profile creation failed"
    }
  ]
}
```

## 🎯 **Expected Response After Fix**

After removing the foreign key constraint, you should get:

### **For New User:**
```json
{
  "success": true,
  "message": "User and profile created successfully",
  "data": {
    "user": {
      "id": "84d0c089-60dd-4e08-80f0-0daf3ce6a63e",
      "email": "mohammed211920@gmail.com",
      "created_at": "2025-09-25T05:14:00.983Z"
    },
    "profile": {
      "id": "84d0c089-60dd-4e08-80f0-0daf3ce6a63e",
      "first_name": "ali",
      "last_name": "mohammed",
      "phone_number": "0509556183",
      "account_type": "personal",
      "created_at": "2025-09-25T05:14:00.983Z"
    }
  },
  "errors": []
}
```

### **For Existing User:**
```json
{
  "success": false,
  "message": "Email already registered",
  "data": null,
  "errors": [
    {
      "field": "email",
      "message": "This email is already in use."
    }
  ]
}
```

## 🚀 **Implementation Details**

### **Database Schema Fix:**
```sql
-- Remove the problematic foreign key constraint
ALTER TABLE profiles DROP CONSTRAINT IF EXISTS profiles_id_fkey;

-- Verify the constraint is removed
SELECT constraint_name, constraint_type 
FROM information_schema.table_constraints 
WHERE table_name = 'profiles' AND constraint_type = 'FOREIGN KEY';
```

### **Enhanced Error Handling:**
The `AuthService` now provides specific error messages for foreign key constraint violations:

```python
if "foreign key constraint" in error_str and "users" in error_str:
    raise ExternalServiceException(
        message="Database configuration error: Foreign key constraint violation",
        field="profile",
        service="Database",
        details={
            "error": "The profiles table has a foreign key constraint referencing a non-existent users table.",
            "solution": "Execute: ALTER TABLE profiles DROP CONSTRAINT IF EXISTS profiles_id_fkey;"
        }
    )
```

## ✅ **Why This Approach Works**

1. **Supabase Integration**: We use Supabase for user authentication, so we don't need a local `users` table
2. **Data Consistency**: The `profiles.id` still corresponds to `auth.users.id` from Supabase
3. **No Data Loss**: Removing the constraint doesn't affect existing data
4. **Clean Architecture**: Aligns with our design of using Supabase for auth and local DB for profiles

## 🔧 **Next Steps**

1. **Execute the SQL fix** in your database
2. **Test the signup endpoint** with the same email
3. **Verify the response** matches the expected format
4. **Confirm profile creation** in the database

The foreign key constraint is the only thing preventing profile creation. Once removed, the clean architecture implementation will work perfectly! 🎯
