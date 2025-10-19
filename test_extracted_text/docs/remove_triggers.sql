-- =====================================================
-- Remove Database Triggers and Functions
-- Run this script in your Supabase SQL editor
-- =====================================================

-- Step 1: Drop triggers
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
DROP TRIGGER IF EXISTS handle_new_user_trigger ON auth.users;

-- Step 2: Drop functions
DROP FUNCTION IF EXISTS public.handle_new_user();
DROP FUNCTION IF EXISTS public.update_updated_at_column();

-- Step 3: Drop trigger for profiles updated_at (if you want to remove it)
DROP TRIGGER IF EXISTS update_profiles_updated_at ON public.profiles;

-- Step 4: Verify triggers and functions are removed
SELECT 
    'Triggers and functions removed successfully' as status,
    COUNT(*) as remaining_triggers
FROM information_schema.triggers 
WHERE trigger_schema = 'public' 
AND trigger_name LIKE '%user%' 
OR trigger_name LIKE '%profile%';

-- Step 5: Check for any remaining functions
SELECT 
    routine_name,
    routine_type
FROM information_schema.routines 
WHERE routine_schema = 'public' 
AND routine_name LIKE '%user%' 
OR routine_name LIKE '%profile%';

-- Step 6: Optional - Remove the updated_at trigger function if you don't want automatic timestamp updates
-- Uncomment the line below if you want to remove the updated_at functionality completely
-- DROP FUNCTION IF EXISTS public.update_updated_at_column();
