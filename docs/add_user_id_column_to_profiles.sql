-- Add user_id column to profiles table
-- This migration adds the user_id column to link profiles to Supabase auth.users

-- Step 1: Add the user_id column
ALTER TABLE profiles 
ADD COLUMN user_id UUID;

-- Step 2: Update existing records to set user_id = id (for existing profiles)
UPDATE profiles 
SET user_id = id 
WHERE user_id IS NULL;

-- Step 3: Make user_id NOT NULL and add unique constraint
ALTER TABLE profiles 
ALTER COLUMN user_id SET NOT NULL;

-- Step 4: Add unique constraint on user_id
ALTER TABLE profiles 
ADD CONSTRAINT uq_profiles_user_id UNIQUE (user_id);

-- Step 5: Add index on user_id for better performance
CREATE INDEX IF NOT EXISTS idx_profiles_user_id ON profiles USING btree (user_id);

-- Step 6: Verify the changes
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM 
    information_schema.columns 
WHERE 
    table_name = 'profiles' 
    AND table_schema = 'public'
ORDER BY ordinal_position;

-- Step 7: Check constraints
SELECT 
    tc.constraint_name,
    tc.constraint_type,
    tc.table_name
FROM 
    information_schema.table_constraints AS tc 
WHERE 
    tc.table_name = 'profiles' 
    AND tc.table_schema = 'public';
