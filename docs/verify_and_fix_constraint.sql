-- Verify and fix the foreign key constraint to properly reference auth.users
-- This script ensures the constraint matches your desired schema

-- Step 1: Check current constraints on profiles table
SELECT 
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    tc.constraint_schema,
    ccu.table_schema AS foreign_table_schema
FROM 
    information_schema.table_constraints AS tc 
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
      AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
      AND ccu.table_schema = tc.constraint_schema
WHERE 
    tc.constraint_type = 'FOREIGN KEY' 
    AND tc.table_name = 'profiles';

-- Step 2: Check if auth.users table exists and is accessible
SELECT 
    table_name, 
    table_schema,
    table_type,
    is_insertable_into
FROM 
    information_schema.tables 
WHERE 
    table_name = 'users' 
    AND table_schema = 'auth';

-- Step 3: Check if there are any users in auth.users
SELECT COUNT(*) as user_count FROM auth.users;

-- Step 4: Check if there are any profiles
SELECT COUNT(*) as profile_count FROM profiles;

-- Step 5: Drop the existing constraint if it exists
ALTER TABLE profiles DROP CONSTRAINT IF EXISTS profiles_id_fkey;

-- Step 6: Recreate the constraint exactly as specified in your schema
ALTER TABLE profiles 
ADD CONSTRAINT profiles_id_fkey 
FOREIGN KEY (id) 
REFERENCES auth.users(id) 
ON UPDATE CASCADE 
ON DELETE CASCADE;

-- Step 7: Verify the constraint was created correctly
SELECT 
    tc.constraint_name,
    tc.table_name,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name,
    tc.constraint_schema,
    ccu.table_schema AS foreign_table_schema
FROM 
    information_schema.table_constraints AS tc 
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
      AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
      AND ccu.table_schema = tc.constraint_schema
WHERE 
    tc.constraint_type = 'FOREIGN KEY' 
    AND tc.table_name = 'profiles';

-- Step 8: Test the constraint by trying to insert a profile with a non-existent user ID
-- This should fail if the constraint is working
-- (Comment out this test after verification)
/*
INSERT INTO profiles (id, first_name, last_name) 
VALUES ('00000000-0000-0000-0000-000000000000', 'test', 'user');
*/
