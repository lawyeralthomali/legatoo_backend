-- Check the actual foreign key constraint definition
-- This will show us what table the constraint is actually referencing

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

-- Also check if there's a users table in the current schema
SELECT table_name, table_schema 
FROM information_schema.tables 
WHERE table_name = 'users';

-- Check if there's a users table in the auth schema
SELECT table_name, table_schema 
FROM information_schema.tables 
WHERE table_name = 'users' AND table_schema = 'auth';
