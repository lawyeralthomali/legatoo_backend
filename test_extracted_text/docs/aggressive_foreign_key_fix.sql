-- Aggressive fix for the foreign key constraint issue
-- This script will forcefully remove all constraints and create the correct one

-- Step 1: Check ALL constraints on profiles table (not just foreign keys)
SELECT 
    tc.constraint_name,
    tc.constraint_type,
    tc.table_name,
    tc.table_schema
FROM 
    information_schema.table_constraints AS tc 
WHERE 
    tc.table_name = 'profiles';

-- Step 2: Get the exact constraint names that exist
SELECT 
    tc.constraint_name,
    tc.constraint_type
FROM 
    information_schema.table_constraints AS tc 
WHERE 
    tc.table_name = 'profiles' 
    AND tc.constraint_type = 'FOREIGN KEY';

-- Step 3: Drop ALL constraints by name (replace with actual names from step 2)
-- This will need to be run with the actual constraint names found in step 2
-- For now, let's try to drop common constraint names
DO $$
DECLARE
    constraint_name TEXT;
BEGIN
    -- Get all foreign key constraint names for profiles table
    FOR constraint_name IN 
        SELECT tc.constraint_name
        FROM information_schema.table_constraints AS tc 
        WHERE tc.table_name = 'profiles' 
        AND tc.constraint_type = 'FOREIGN KEY'
    LOOP
        EXECUTE 'ALTER TABLE profiles DROP CONSTRAINT IF EXISTS ' || constraint_name;
        RAISE NOTICE 'Dropped constraint: %', constraint_name;
    END LOOP;
END $$;

-- Step 4: Verify ALL constraints are removed
SELECT 
    tc.constraint_name,
    tc.constraint_type,
    tc.table_name
FROM 
    information_schema.table_constraints AS tc 
WHERE 
    tc.table_name = 'profiles';

-- Step 5: Check if auth.users table exists and is accessible
SELECT 
    table_name, 
    table_schema,
    table_type
FROM 
    information_schema.tables 
WHERE 
    table_name = 'users' 
    AND table_schema = 'auth';

-- Step 6: Try to create the constraint with explicit schema reference
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
