-- Update subscription model to match the new Python model
-- Run this in Supabase SQL Editor after running database_setup_new.sql

-- Create the subscription status enum type
CREATE TYPE subscription_status_enum AS ENUM ('active', 'expired', 'cancelled');

-- Add current_usage column to subscriptions table (if it doesn't exist)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns 
        WHERE table_name = 'subscriptions' 
        AND column_name = 'current_usage'
    ) THEN
        ALTER TABLE public.subscriptions 
        ADD COLUMN current_usage JSONB DEFAULT '{}';
    END IF;
END $$;

-- Update the status column to use the enum type
ALTER TABLE public.subscriptions 
ALTER COLUMN status TYPE subscription_status_enum 
USING status::subscription_status_enum;

-- Update existing subscriptions to use enum values
UPDATE public.subscriptions 
SET status = 'active'::subscription_status_enum 
WHERE status = 'active';

UPDATE public.subscriptions 
SET status = 'expired'::subscription_status_enum 
WHERE status = 'expired';

UPDATE public.subscriptions 
SET status = 'cancelled'::subscription_status_enum 
WHERE status = 'cancelled';

-- Update the handle_new_user function to include current_usage
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
            'active'::subscription_status_enum,
            '{}'
        );
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Add comments
COMMENT ON TYPE subscription_status_enum IS 'Subscription status enumeration: active, expired, cancelled';
COMMENT ON COLUMN public.subscriptions.current_usage IS 'Current usage tracking in JSONB format';
COMMENT ON COLUMN public.subscriptions.status IS 'Subscription status using enum type';

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_subscriptions_status_enum ON public.subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_current_usage ON public.subscriptions USING GIN (current_usage);

