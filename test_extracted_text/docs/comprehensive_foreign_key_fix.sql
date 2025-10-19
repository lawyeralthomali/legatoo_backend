-- Comprehensive fix for the foreign key constraint issue
-- This script ensures the constraint properly references auth.users

-- Step 1: Check current constraints
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

-- Step 2: Drop ALL possible foreign key constraints
ALTER TABLE profiles DROP CONSTRAINT IF EXISTS profiles_id_fkey;
ALTER TABLE profiles DROP CONSTRAINT IF EXISTS profiles_user_id_fkey;
ALTER TABLE profiles DROP CONSTRAINT IF EXISTS profiles_users_fkey;
ALTER TABLE profiles DROP CONSTRAINT IF EXISTS profiles_id_fkey_1;
ALTER TABLE profiles DROP CONSTRAINT IF EXISTS profiles_id_fkey_2;

-- Step 3: Verify constraints are removed
SELECT 
    tc.constraint_name,
    tc.constraint_type,
    tc.table_name
FROM 
    information_schema.table_constraints AS tc 
WHERE 
    tc.table_name = 'profiles' 
    AND tc.constraint_type = 'FOREIGN KEY';

-- Step 4: Check if auth.users table exists and is accessible
SELECT 
    table_name, 
    table_schema,
    table_type
FROM 
    information_schema.tables 
WHERE 
    table_name = 'users' 
    AND table_schema = 'auth';

-- Step 5: Try to create the constraint with explicit schema reference
-- This should work if auth.users is accessible
ALTER TABLE profiles 
ADD CONSTRAINT profiles_id_fkey 
FOREIGN KEY (id) 
REFERENCES auth.users(id) 
ON UPDATE CASCADE 
ON DELETE CASCADE;

-- Step 6: Verify the constraint was created correctly
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
