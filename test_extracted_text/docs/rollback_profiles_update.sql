-- =====================================================
-- Rollback Profiles Table Update
-- Use this script to revert the profile table changes
-- =====================================================

-- WARNING: This will remove the new columns and data!
-- Make sure you have a backup before running this script.

-- Step 1: Drop triggers
DROP TRIGGER IF EXISTS update_profiles_updated_at ON public.profiles;

-- Step 2: Drop functions
DROP FUNCTION IF EXISTS public.update_updated_at_column();

-- Step 3: Drop constraints
ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS check_first_name_length;
ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS check_last_name_length;
ALTER TABLE public.profiles DROP CONSTRAINT IF EXISTS check_phone_number_length;

-- Step 4: Drop indexes
DROP INDEX IF EXISTS idx_profiles_first_name;
DROP INDEX IF EXISTS idx_profiles_last_name;
DROP INDEX IF EXISTS idx_profiles_account_type;
DROP INDEX IF EXISTS idx_profiles_created_at;

-- Step 5: Add back full_name column if it was removed
ALTER TABLE public.profiles 
ADD COLUMN IF NOT EXISTS full_name TEXT;

-- Step 6: Reconstruct full_name from first_name and last_name
UPDATE public.profiles 
SET full_name = CONCAT(first_name, ' ', last_name)
WHERE first_name IS NOT NULL AND last_name IS NOT NULL;

-- Step 7: Add back bio column if it was removed
ALTER TABLE public.profiles 
ADD COLUMN IF NOT EXISTS bio TEXT;

-- Step 8: Remove new columns (UNCOMMENT WHEN READY TO REMOVE)
-- ALTER TABLE public.profiles DROP COLUMN IF EXISTS first_name;
-- ALTER TABLE public.profiles DROP COLUMN IF EXISTS last_name;
-- ALTER TABLE public.profiles DROP COLUMN IF EXISTS phone_number;
-- ALTER TABLE public.profiles DROP COLUMN IF EXISTS created_at;
-- ALTER TABLE public.profiles DROP COLUMN IF EXISTS updated_at;

-- Step 9: Verify rollback
SELECT 'Rollback completed' as status, COUNT(*) as profiles_rolled_back FROM public.profiles;
