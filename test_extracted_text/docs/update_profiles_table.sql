-- =====================================================
-- Update Profiles Table Structure
-- Run this script in your Supabase SQL editor
-- =====================================================

-- Step 1: Add new columns
ALTER TABLE public.profiles 
ADD COLUMN IF NOT EXISTS first_name TEXT,
ADD COLUMN IF NOT EXISTS last_name TEXT,
ADD COLUMN IF NOT EXISTS phone_number TEXT;

-- Step 2: Migrate existing data from full_name to first_name and last_name
-- Split full_name into first_name and last_name for existing records
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
    END
WHERE first_name IS NULL OR last_name IS NULL;

-- Step 3: Make first_name and last_name NOT NULL
ALTER TABLE public.profiles 
ALTER COLUMN first_name SET NOT NULL,
ALTER COLUMN last_name SET NOT NULL;

-- Step 4: Add constraints for field lengths
ALTER TABLE public.profiles 
ADD CONSTRAINT check_first_name_length CHECK (length(first_name) >= 1 AND length(first_name) <= 100),
ADD CONSTRAINT check_last_name_length CHECK (length(last_name) >= 1 AND length(last_name) <= 100),
ADD CONSTRAINT check_phone_number_length CHECK (phone_number IS NULL OR length(phone_number) <= 20);

-- Step 5: Add proper timestamps if they don't exist
ALTER TABLE public.profiles 
ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
ADD COLUMN IF NOT EXISTS updated_at TIMESTAMP WITH TIME ZONE;

-- Step 6: Update existing records to have created_at timestamp
UPDATE public.profiles 
SET created_at = NOW() 
WHERE created_at IS NULL;

-- Step 7: Make created_at NOT NULL
ALTER TABLE public.profiles 
ALTER COLUMN created_at SET NOT NULL;

-- Step 8: Create a function to automatically update updated_at
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Step 9: Create trigger to automatically update updated_at
DROP TRIGGER IF EXISTS update_profiles_updated_at ON public.profiles;
CREATE TRIGGER update_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- Step 10: Update the handle_new_user function to use new structure
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
DECLARE
    trial_plan_id UUID;
    user_first_name TEXT;
    user_last_name TEXT;
    user_phone_number TEXT;
BEGIN
    -- Extract user data from metadata
    user_first_name := COALESCE(NEW.raw_user_meta_data->>'first_name', 'User');
    user_last_name := COALESCE(NEW.raw_user_meta_data->>'last_name', 'User');
    user_phone_number := NEW.raw_user_meta_data->>'phone_number';
    
    -- Insert a new profile for the user
    INSERT INTO public.profiles (
        id, 
        first_name, 
        last_name, 
        avatar_url, 
        phone_number, 
        account_type,
        created_at
    )
    VALUES (
        NEW.id,
        user_first_name,
        user_last_name,
        NEW.raw_user_meta_data->>'avatar_url',
        user_phone_number,
        'personal',
        NOW()
    );
    
    -- Get the trial plan ID
    SELECT plan_id INTO trial_plan_id 
    FROM public.plans 
    WHERE plan_type = 'free' AND is_active = true 
    LIMIT 1;
    
    -- Create a trial subscription for the new user
    IF trial_plan_id IS NOT NULL THEN
        INSERT INTO public.subscriptions (user_id, plan_id, start_date, end_date, status)
        VALUES (
            NEW.id,
            trial_plan_id,
            NOW(),
            NOW() + INTERVAL '7 days',
            'active'
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Step 11: Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_profiles_first_name ON public.profiles(first_name);
CREATE INDEX IF NOT EXISTS idx_profiles_last_name ON public.profiles(last_name);
CREATE INDEX IF NOT EXISTS idx_profiles_account_type ON public.profiles(account_type);
CREATE INDEX IF NOT EXISTS idx_profiles_created_at ON public.profiles(created_at);

-- Step 12: Add comments for documentation
COMMENT ON COLUMN public.profiles.first_name IS 'User first name (1-100 characters)';
COMMENT ON COLUMN public.profiles.last_name IS 'User last name (1-100 characters)';
COMMENT ON COLUMN public.profiles.phone_number IS 'User phone number (max 20 characters)';
COMMENT ON COLUMN public.profiles.created_at IS 'Profile creation timestamp';
COMMENT ON COLUMN public.profiles.updated_at IS 'Profile last update timestamp';

-- Step 13: Optional - Remove old columns after verification (UNCOMMENT WHEN READY)
-- WARNING: This will permanently delete the full_name and bio columns
-- Make sure to backup your data before running this!

-- ALTER TABLE public.profiles DROP COLUMN IF EXISTS full_name;
-- ALTER TABLE public.profiles DROP COLUMN IF EXISTS bio;

-- Step 14: Verify the migration
-- Run this query to verify the migration was successful:
SELECT 
    'Migration completed successfully' as status,
    COUNT(*) as total_profiles,
    COUNT(CASE WHEN first_name IS NOT NULL AND last_name IS NOT NULL THEN 1 END) as profiles_with_names,
    COUNT(CASE WHEN phone_number IS NOT NULL THEN 1 END) as profiles_with_phone,
    COUNT(CASE WHEN created_at IS NOT NULL THEN 1 END) as profiles_with_timestamps
FROM public.profiles;
