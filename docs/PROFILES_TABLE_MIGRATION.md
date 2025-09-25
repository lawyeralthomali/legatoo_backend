# Profiles Table Migration - Add user_id Column

## ✅ **Issue Identified**

The database table `profiles` doesn't have a `user_id` column, but our SQLAlchemy model is trying to insert into it. The error shows:

```
column "user_id" of relation "profiles" does not exist
```

## 🔍 **Current Database Schema**

The current `profiles` table has:
```sql
create table public.profiles (
  id uuid not null,
  avatar_url text null,
  account_type public.account_type_enum null default 'personal'::account_type_enum,
  created_at timestamp with time zone not null default now(),
  updated_at timestamp with time zone null,
  first_name text not null,
  last_name text not null,
  phone_number text null,
  constraint profiles_pkey primary key (id),
  -- ... other constraints
);
```

## 🔧 **Solution Applied**

### **1. Database Migration Script**
Created `docs/add_user_id_column_to_profiles.sql` to:
- Add `user_id` column to the `profiles` table
- Update existing records to set `user_id = id`
- Make `user_id` NOT NULL and add unique constraint
- Add index on `user_id` for better performance

### **2. Temporary Model Updates**
Updated the Profile model to work with the current database schema:
- Commented out `user_id` column temporarily
- Updated ProfileRepository to not include `user_id` in inserts
- Made `user_id` optional in ProfileResponse schema
- Added fallback logic to use `id` when `user_id` is not available

## 🎯 **Migration Steps**

### **Step 1: Apply Database Migration**
Execute the migration script:
```sql
-- Run: docs/add_user_id_column_to_profiles.sql
```

### **Step 2: Update Model After Migration**
After the migration is applied, uncomment the `user_id` column in the Profile model:
```python
# Uncomment this line in app/models/profile.py
user_id = Column(UUID(as_uuid=True), nullable=False, unique=True, index=True)
```

### **Step 3: Update Repository After Migration**
After the migration is applied, uncomment the user_id assignment in ProfileRepository:
```python
# Uncomment this line in app/repositories/profile_repository.py
profile_dict["user_id"] = user_id  # User ID from Supabase
```

### **Step 4: Update Schema After Migration**
After the migration is applied, make user_id required in ProfileResponse:
```python
# Change this line in app/schemas/profile.py
user_id: UUID = Field(..., description="User ID from Supabase auth.users")
```

## 🚀 **Expected Behavior After Migration**

### **For New User:**
```json
{
  "success": true,
  "message": "User and profile created successfully",
  "data": {
    "user": {
      "id": "new-uuid-here",
      "email": "mohammed211920@gmail.com",
      "created_at": "2025-09-25T05:55:16.133Z"
    },
    "profile": {
      "id": "new-uuid-here",
      "user_id": "new-uuid-here",
      "first_name": "ali",
      "last_name": "mohammed",
      "phone_number": "0509556183",
      "account_type": "personal",
      "created_at": "2025-09-25T05:55:16.133Z"
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

## 📋 **Files Modified**

1. **`docs/add_user_id_column_to_profiles.sql`** - Database migration script
2. **`app/models/profile.py`** - Temporarily commented out user_id column
3. **`app/repositories/profile_repository.py`** - Temporarily commented out user_id assignment
4. **`app/schemas/profile.py`** - Made user_id optional temporarily
5. **`app/services/auth_service_new.py`** - Added fallback logic for user_id

## ✅ **Next Steps**

1. **Execute the migration script**: `docs/add_user_id_column_to_profiles.sql`
2. **Uncomment the user_id column** in the Profile model
3. **Uncomment the user_id assignment** in ProfileRepository
4. **Make user_id required** in ProfileResponse schema
5. **Test the signup endpoint** to ensure it works correctly

## 🎯 **Why This Approach Works**

- **Backward Compatible**: Works with existing database schema
- **Gradual Migration**: Allows the application to run during migration
- **Data Integrity**: Ensures user_id is properly set for all profiles
- **Performance**: Adds index on user_id for better query performance
- **Unique Constraint**: Prevents duplicate profiles for the same user

The migration will add the `user_id` column while preserving all existing data and ensuring the application continues to work! 🎯
