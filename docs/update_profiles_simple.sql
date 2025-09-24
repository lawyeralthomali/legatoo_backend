-- =====================================================
-- Simple Profiles Table Update
-- Run this script in your Supabase SQL editor
-- =====================================================

-- Add new columns
ALTER TABLE public.profiles 
ADD COLUMN first_name TEXT,
ADD COLUMN last_name TEXT,
ADD COLUMN phone_number TEXT,
ADD COLUMN created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
ADD COLUMN updated_at TIMESTAMP WITH TIME ZONE;

-- Migrate existing full_name data
UPDATE public.profiles 
SET 
    first_name = CASE 
        WHEN full_name IS NULL OR full_name = '' THEN 'User'
        WHEN position(' ' in full_name) = 0 THEN full_name
        ELSE split_part(full_name, ' ', 1)
    END,
    last_name = CASE 
        WHEN full_name IS NULL OR full_name = '' THEN 'User'
        WHEN position(' ' in full_name) = 0 THEN 'User'
        ELSE substring(full_name from position(' ' in full_name) + 1)
    END,
    created_at = NOW()
WHERE first_name IS NULL;

-- Make required fields NOT NULL
ALTER TABLE public.profiles 
ALTER COLUMN first_name SET NOT NULL,
ALTER COLUMN last_name SET NOT NULL,
ALTER COLUMN created_at SET NOT NULL;

-- Add field length constraints
ALTER TABLE public.profiles 
ADD CONSTRAINT check_first_name_length CHECK (length(first_name) >= 1 AND length(first_name) <= 100),
ADD CONSTRAINT check_last_name_length CHECK (length(last_name) >= 1 AND length(last_name) <= 100),
ADD CONSTRAINT check_phone_number_length CHECK (phone_number IS NULL OR length(phone_number) <= 20);

-- Create updated_at trigger
CREATE OR REPLACE FUNCTION public.update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_profiles_updated_at
    BEFORE UPDATE ON public.profiles
    FOR EACH ROW
    EXECUTE FUNCTION public.update_updated_at_column();

-- Verify migration
SELECT 'Migration completed' as status, COUNT(*) as profiles_updated FROM public.profiles;
