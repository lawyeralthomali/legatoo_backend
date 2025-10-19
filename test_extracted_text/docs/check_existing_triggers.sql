-- =====================================================
-- Check Existing Triggers and Functions
-- Run this script to see what triggers/functions exist
-- =====================================================

-- Check all triggers in the database
SELECT 
    trigger_name,
    event_manipulation,
    event_object_table,
    action_statement,
    trigger_schema
FROM information_schema.triggers 
WHERE trigger_schema IN ('public', 'auth')
ORDER BY trigger_schema, trigger_name;

-- Check all functions in the public schema
SELECT 
    routine_name,
    routine_type,
    data_type,
    routine_definition
FROM information_schema.routines 
WHERE routine_schema = 'public'
ORDER BY routine_name;

-- Check specifically for user-related triggers
SELECT 
    trigger_name,
    event_object_table,
    action_statement
FROM information_schema.triggers 
WHERE trigger_schema = 'auth' 
AND event_object_table = 'users';

-- Check for profile-related triggers
SELECT 
    trigger_name,
    event_object_table,
    action_statement
FROM information_schema.triggers 
WHERE trigger_schema = 'public' 
AND event_object_table = 'profiles';

-- Check for handle_new_user function specifically
SELECT 
    routine_name,
    routine_type,
    routine_definition
FROM information_schema.routines 
WHERE routine_schema = 'public'
AND routine_name LIKE '%user%';

-- Summary
SELECT 
    'Summary' as info,
    COUNT(*) as total_triggers
FROM information_schema.triggers 
WHERE trigger_schema IN ('public', 'auth')
UNION ALL
SELECT 
    'Summary' as info,
    COUNT(*) as total_functions
FROM information_schema.routines 
WHERE routine_schema = 'public';
