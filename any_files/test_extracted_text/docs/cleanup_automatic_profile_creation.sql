-- =====================================================
-- Complete Cleanup of Automatic Profile Creation
-- Run this script to remove all automatic profile creation logic
-- =====================================================

-- Step 1: Remove all triggers related to user creation
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP TRIGGER IF EXISTS handle_new_user_trigger ON auth.users;
DROP TRIGGER IF EXISTS auth_user_created ON auth.users;

-- Step 2: Remove all functions related to automatic profile creation
DROP FUNCTION IF EXISTS public.handle_new_user();
DROP FUNCTION IF EXISTS public.create_user_profile();
DROP FUNCTION IF EXISTS public.on_auth_user_created();

-- Step 3: Remove the updated_at trigger (optional - uncomment if you want to remove it)
-- DROP TRIGGER IF EXISTS update_profiles_updated_at ON public.profiles;
-- DROP FUNCTION IF EXISTS public.update_updated_at_column();

-- Step 4: Check what's left
SELECT 
    'Remaining triggers:' as info,
    trigger_name,
    event_object_table,
    trigger_schema
FROM information_schema.triggers 
WHERE trigger_schema IN ('public', 'auth')
ORDER BY trigger_schema, trigger_name;

-- Step 5: Check remaining functions
SELECT 
    'Remaining functions:' as info,
    routine_name,
    routine_type
FROM information_schema.routines 
WHERE routine_schema = 'public'
ORDER BY routine_name;

-- Step 6: Verify profiles table structure
SELECT 
    column_name,
    data_type,
    is_nullable,
    column_default
FROM information_schema.columns 
WHERE table_schema = 'public' 
AND table_name = 'profiles'
ORDER BY ordinal_position;

-- Step 7: Check if there are any constraints or indexes to clean up
SELECT 
    'Constraints:' as info,
    constraint_name,
    constraint_type
FROM information_schema.table_constraints 
WHERE table_schema = 'public' 
AND table_name = 'profiles';

SELECT 
    'Indexes:' as info,
    indexname,
    indexdef
FROM pg_indexes 
WHERE schemaname = 'public' 
AND tablename = 'profiles';

-- Step 8: Final verification
SELECT 
    'Cleanup completed' as status,
    'All automatic profile creation triggers and functions have been removed' as message;
