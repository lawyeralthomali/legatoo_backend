-- Alternative solution: Remove the foreign key constraint entirely
-- Since we're using Supabase for authentication, we can rely on application-level validation

-- Drop ALL foreign key constraints on the profiles table
ALTER TABLE profiles DROP CONSTRAINT IF EXISTS profiles_id_fkey;
ALTER TABLE profiles DROP CONSTRAINT IF EXISTS profiles_user_id_fkey;
ALTER TABLE profiles DROP CONSTRAINT IF EXISTS profiles_users_fkey;

-- Verify all foreign key constraints are removed
SELECT 
    tc.constraint_name,
    tc.constraint_type,
    tc.table_name
FROM 
    information_schema.table_constraints AS tc 
WHERE 
    tc.table_name = 'profiles' 
    AND tc.constraint_type = 'FOREIGN KEY';

-- The profiles table should now work without foreign key constraints
-- We'll rely on application-level validation to ensure data integrity
