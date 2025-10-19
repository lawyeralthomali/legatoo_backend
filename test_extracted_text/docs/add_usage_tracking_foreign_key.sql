-- Add foreign key constraint for usage_tracking table
-- Run this in Supabase SQL Editor after running database_setup_new.sql

-- Add foreign key constraint for usage_tracking.subscription_id
ALTER TABLE public.usage_tracking 
ADD CONSTRAINT usage_tracking_subscription_id_fkey 
FOREIGN KEY (subscription_id) REFERENCES public.subscriptions(subscription_id) ON DELETE CASCADE;

-- Add foreign key constraint for billing.subscription_id (if not already exists)
DO $$ 
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.table_constraints 
        WHERE constraint_name = 'billing_subscription_id_fkey'
    ) THEN
        ALTER TABLE public.billing 
        ADD CONSTRAINT billing_subscription_id_fkey 
        FOREIGN KEY (subscription_id) REFERENCES public.subscriptions(subscription_id) ON DELETE CASCADE;
    END IF;
END $$;

-- Update the handle_new_user function to create usage tracking records
CREATE OR REPLACE FUNCTION public.handle_new_user()
RETURNS TRIGGER AS $$
DECLARE
    trial_plan_id UUID;
    new_subscription_id UUID;
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
        INSERT INTO public.subscriptions (user_id, plan_id, start_date, end_date, status)
        VALUES (
            NEW.id,
            trial_plan_id,
            NOW(),
            NOW() + INTERVAL '7 days',
            'active'::subscription_status_enum
        )
        RETURNING subscription_id INTO new_subscription_id;
        
        -- Create usage tracking records for common features
        INSERT INTO public.usage_tracking (subscription_id, feature, used_count, reset_cycle)
        VALUES 
            (new_subscription_id, 'file_upload', 0, 'monthly'),
            (new_subscription_id, 'ai_chat', 0, 'monthly'),
            (new_subscription_id, 'contract', 0, 'monthly'),
            (new_subscription_id, 'report', 0, 'monthly'),
            (new_subscription_id, 'token', 0, 'monthly'),
            (new_subscription_id, 'multi_user', 0, 'monthly');
    END IF;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Add comments
COMMENT ON CONSTRAINT usage_tracking_subscription_id_fkey ON public.usage_tracking IS 'Foreign key to subscriptions table';
COMMENT ON CONSTRAINT billing_subscription_id_fkey ON public.billing IS 'Foreign key to subscriptions table';
