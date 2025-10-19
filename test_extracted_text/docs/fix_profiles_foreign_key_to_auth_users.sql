-- Fix profiles table foreign key constraint to reference auth.users
-- This script updates the foreign key constraint to properly reference Supabase's auth.users table

-- First, drop the existing foreign key constraint
ALTER TABLE profiles DROP CONSTRAINT IF EXISTS profiles_id_fkey;

-- Add the correct foreign key constraint that references auth.users
ALTER TABLE profiles 
ADD CONSTRAINT profiles_id_fkey 
FOREIGN KEY (id) 
REFERENCES auth.users(id) 
ON UPDATE CASCADE 
ON DELETE CASCADE;

-- Verify the constraint was created correctly
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
