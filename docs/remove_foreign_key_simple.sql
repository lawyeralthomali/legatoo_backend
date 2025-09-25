-- Simple solution: Remove the foreign key constraint entirely
-- This is the most reliable approach for Supabase integration

-- Step 1: Check what constraints currently exist
SELECT 
    tc.constraint_name,
    tc.constraint_type,
    tc.table_name
FROM 
    information_schema.table_constraints AS tc 
WHERE 
    tc.table_name = 'profiles';

-- Step 2: Drop ALL foreign key constraints using a dynamic approach
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

-- Step 3: Verify all foreign key constraints are removed
SELECT 
    tc.constraint_name,
    tc.constraint_type,
    tc.table_name
FROM 
    information_schema.table_constraints AS tc 
WHERE 
    tc.table_name = 'profiles' 
    AND tc.constraint_type = 'FOREIGN KEY';

-- Step 4: Verify the profiles table structure
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
