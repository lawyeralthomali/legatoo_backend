-- =====================================================
-- Cleanup Script: Remove Old Subscription System
-- Run this in Supabase SQL Editor after migrating to new system
-- =====================================================

-- Step 1: Drop the old user_subscriptions table
DROP TABLE IF EXISTS public.user_subscriptions CASCADE;

-- Step 2: Update the handle_new_user function to use the new subscription system
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
DECLARE
    trial_plan_id UUID;
BEGIN
    -- Insert a new profile for the user
    INSERT INTO public.profiles (id, full_name, avatar_url, bio, ccount_type)
    VALUES (
        NEW.id,
        COALESCE(NEW.raw_user_meta_data->>'full_name', 'User'),
        NEW.raw_user_meta_data->>'avatar_url',
        NEW.raw_user_meta_data->>'bio',
        'personal'
    );
    
    -- Get the trial plan ID from the new subscription system
    SELECT plan_id INTO trial_plan_id 
    FROM public.plans 
    WHERE plan_type = 'free' AND is_active = true 
    LIMIT 1;
    
    -- Create a trial subscription for the new user using the new system
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

-- Step 3: Verify cleanup
SELECT 
    'Cleanup Complete' as status,
    'Old user_subscriptions table removed' as message,
    'New subscription system is now active' as next_step;

-- Step 4: Show current tables
SELECT 
    table_name,
    table_type
FROM information_schema.tables 
WHERE table_schema = 'public' 
AND table_name IN ('profiles', 'plans', 'subscriptions', 'usage_tracking', 'billing')
ORDER BY table_name;

-- =====================================================
-- Cleanup Complete!
-- =====================================================

/*
The old subscription system has been completely removed and replaced with the new enhanced system.

New system includes:
- plans: Subscription plans with features and limits
- subscriptions: User subscriptions linked to plans  
- usage_tracking: Feature usage monitoring
- billing: Invoices and payment tracking

All new users will automatically get a trial subscription using the new system.
*/
