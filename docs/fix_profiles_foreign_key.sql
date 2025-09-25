-- Fix profiles table foreign key constraint
-- This script removes the foreign key constraint that references a non-existent users table

-- Drop the foreign key constraint
ALTER TABLE profiles DROP CONSTRAINT IF EXISTS profiles_id_fkey;

-- The profiles table should now work without referencing a local users table
-- The id field will still be a UUID that corresponds to Supabase auth.users.id
-- but without the foreign key constraint that requires a local users table
