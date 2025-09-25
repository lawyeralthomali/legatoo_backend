-- Debug the profiles table and check for any existing data or constraints

-- Check if there are any existing profiles
SELECT COUNT(*) as profile_count FROM profiles;

-- Check if there are any profiles with the specific user ID
SELECT * FROM profiles WHERE id = '84d0c089-60dd-4e08-80f0-0daf3ce6a63e';

-- Check all constraints on the profiles table
SELECT 
    tc.constraint_name,
    tc.constraint_type,
    tc.table_name,
    tc.table_schema
FROM 
    information_schema.table_constraints AS tc 
WHERE 
    tc.table_name = 'profiles';

-- Check if the user exists in auth.users
SELECT id, email, created_at FROM auth.users WHERE id = '84d0c089-60dd-4e08-80f0-0daf3ce6a63e';

-- Check if the user exists in auth.users by email
SELECT id, email, created_at FROM auth.users WHERE email = 'mohammed211920@gmail.com';
