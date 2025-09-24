-- Add account_type enum to profiles table
-- Run this in Supabase SQL Editor after running database_setup_new.sql

-- Create the account_type enum type
CREATE TYPE account_type_enum AS ENUM ('personal', 'business');

-- Add the account_type column to profiles table
ALTER TABLE public.profiles 
ADD COLUMN account_type account_type_enum DEFAULT 'personal';

-- Update existing profiles to have 'personal' account type
UPDATE public.profiles 
SET account_type = 'personal' 
WHERE account_type IS NULL;

-- Make the column NOT NULL after setting defaults
ALTER TABLE public.profiles 
ALTER COLUMN account_type SET NOT NULL;

-- Update the handle_new_user function to include account_type
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
DECLARE
    trial_plan_id UUID;
BEGIN
    -- Insert a new profile for the user
    INSERT INTO public.profiles (id, full_name, avatar_url, bio, account_type)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'full_name', 'User'),
        NEW.raw_user_meta_data->>'avatar_url',
        NEW.raw_user_meta_data->>'bio',
        'personal'
    );
    
    -- Get the trial plan ID
    SELECT plan_id INTO trial_plan_id 
    FROM public.plans 
    WHERE plan_type = 'free' AND is_active = true 
    LIMIT 1;
    
    -- Create a trial subscription for the new user
    IF trial_plan_id IS NOT NULL THEN
        INSERT INTO public.subscriptions (user_id, plan_id, start_date, end_date, status, current_usage)
        VALUES (
            NEW.id,
            trial_plan_id,
            NOW(),
            NOW() + INTERVAL '7 days',
            'active',
            '{}'
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Add comment to the enum type
COMMENT ON TYPE account_type_enum IS 'Account type enumeration: personal or business';

-- Add comment to the column
COMMENT ON COLUMN public.profiles.account_type IS 'Account type: personal or business';
