-- =====================================================
-- Update Profiles Table Structure (No Triggers)
-- Run this script in your Supabase SQL editor
-- =====================================================

-- Step 1: Add new columns
ALTER TABLE public.profiles 
ADD COLUMN IF NOT EXISTS first_name TEXT,
ADD COLUMN IF NOT EXISTS last_name TEXT,
ADD COLUMN IF NOT EXISTS phone_number TEXT,
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE;

-- Step 2: Migrate existing full_name data
UPDATE public.profiles 
SET 
    first_name = CASE 
        WHEN full_name IS NULL OR full_name = '' THEN 'User'
        WHEN position(' ' in full_name) = 0 THEN full_name  -- No space, use as first_name
        ELSE split_part(full_name, ' ', 1)  -- First part as first_name
    END,
    last_name = CASE 
        WHEN full_name IS NULL OR full_name = '' THEN 'User'
        WHEN position(' ' in full_name) = 0 THEN 'User'  -- No space, default last_name
        ELSE substring(full_name from position(' ' in full_name) + 1)  -- Rest as last_name
    END,
    created_at = NOW()
WHERE first_name IS NULL OR last_name IS NULL;

-- Step 3: Make required fields NOT NULL
ALTER TABLE public.profiles 
ALTER COLUMN first_name SET NOT NULL,
ALTER COLUMN last_name SET NOT NULL,
ALTER COLUMN created_at SET NOT NULL;

-- Step 4: Add constraints for field lengths
ALTER TABLE public.profiles 
ADD CONSTRAINT check_first_name_length CHECK (length(first_name) >= 1 AND length(first_name) <= 100),
ADD CONSTRAINT check_last_name_length CHECK (length(last_name) >= 1 AND length(last_name) <= 100),
ADD CONSTRAINT check_phone_number_length CHECK (phone_number IS NULL OR length(phone_number) <= 20);

-- Step 5: Create a function to automatically update updated_at
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Step 6: Create trigger to automatically update updated_at
DROP TRIGGER IF EXISTS update_profiles_updated_at ON public.profiles;
CREATE TRIGGER update_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- Step 7: Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_profiles_first_name ON public.profiles(first_name);
CREATE INDEX IF NOT EXISTS idx_profiles_last_name ON public.profiles(last_name);
CREATE INDEX IF NOT EXISTS idx_profiles_account_type ON public.profiles(account_type);
CREATE INDEX IF NOT EXISTS idx_profiles_created_at ON public.profiles(created_at);

-- Step 8: Add comments for documentation
COMMENT ON COLUMN public.profiles.first_name IS 'User first name (1-100 characters)';
COMMENT ON COLUMN public.profiles.last_name IS 'User last name (1-100 characters)';
COMMENT ON COLUMN public.profiles.phone_number IS 'User phone number (max 20 characters)';
COMMENT ON COLUMN public.profiles.created_at IS 'Profile creation timestamp';
COMMENT ON COLUMN public.profiles.updated_at IS 'Profile last update timestamp';

-- Step 9: Verify the migration
SELECT 
    'Migration completed successfully' as status,
    COUNT(*) as total_profiles,
    COUNT(CASE WHEN first_name IS NOT NULL AND last_name IS NOT NULL THEN 1 END) as profiles_with_names,
    COUNT(CASE WHEN phone_number IS NOT NULL THEN 1 END) as profiles_with_phone,
    COUNT(CASE WHEN created_at IS NOT NULL THEN 1 END) as profiles_with_timestamps
FROM public.profiles;

-- Step 10: Optional - Remove old columns after verification (UNCOMMENT WHEN READY)
-- WARNING: This will permanently delete the full_name and bio columns
-- Make sure to backup your data before running this!

-- ALTER TABLE public.profiles DROP COLUMN IF EXISTS full_name;
-- ALTER TABLE public.profiles DROP COLUMN IF EXISTS bio;
