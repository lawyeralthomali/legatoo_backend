-- =====================================================
-- Enhanced Subscription System Database Setup
-- Run this script in your Supabase SQL editor
-- =====================================================

-- Create plans table
CREATE TABLE IF NOT EXISTS public.plans (
    plan_id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    plan_name TEXT NOT NULL,               -- Free Trial, Monthly, Annual
    plan_type TEXT NOT NULL,               -- free, monthly, annual
    price NUMERIC(10,2) NOT NULL DEFAULT 0, -- السعر (0 للـ Free)
    billing_cycle TEXT NOT NULL,           -- monthly / yearly / none
    file_limit INTEGER,                    -- عدد الملفات المسموح
    ai_message_limit INTEGER,              -- عدد الرسائل
    contract_limit INTEGER,                -- عدد العقود
    report_limit INTEGER,                  -- عدد التقارير القابلة للتصدير
    token_limit INTEGER,                   -- حد التوكنات
    multi_user_limit INTEGER,              -- عدد المستخدمين المسموح
    government_integration BOOLEAN DEFAULT FALSE,
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE
);

-- Create enum types
CREATE TYPE subscription_status_enum AS ENUM ('active', 'expired', 'cancelled');
CREATE TYPE account_type_enum AS ENUM ('personal', 'business');

-- Create profiles table (if not exists)
CREATE TABLE IF NOT EXISTS public.profiles (
    id UUID PRIMARY KEY,                   -- References auth.users.id
    full_name TEXT NOT NULL,
    avatar_url TEXT,
    bio TEXT,
    account_type account_type_enum DEFAULT 'personal',
    created_at TIMESTAMP WITH TIME ZONE NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE
);

-- Create subscriptions table
CREATE TABLE IF NOT EXISTS public.subscriptions (
    subscription_id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE,
    plan_id UUID REFERENCES public.plans(plan_id) ON DELETE RESTRICT,
    start_date TIMESTAMP NOT NULL DEFAULT NOW(),
    end_date TIMESTAMP,                    -- تاريخ انتهاء الاشتراك
    auto_renew BOOLEAN DEFAULT TRUE,
    status subscription_status_enum NOT NULL DEFAULT 'active'  -- active, expired, cancelled
);

-- Create usage_tracking table
CREATE TABLE IF NOT EXISTS public.usage_tracking (
    usage_id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    subscription_id UUID REFERENCES public.subscriptions(subscription_id) ON DELETE CASCADE,
    feature TEXT NOT NULL,                 -- file_upload, ai_chat, contract, token
    used_count INTEGER NOT NULL DEFAULT 0,
    reset_cycle TEXT NOT NULL,             -- daily / monthly / yearly
    last_reset TIMESTAMP DEFAULT NOW(),
    UNIQUE(subscription_id, feature)       -- Ensure one record per subscription per feature
);

-- Create billing table
CREATE TABLE IF NOT EXISTS public.billing (
    invoice_id UUID PRIMARY KEY DEFAULT extensions.uuid_generate_v4(),
    subscription_id UUID REFERENCES public.subscriptions(subscription_id) ON DELETE CASCADE,
    amount NUMERIC(10,2) NOT NULL,
    currency TEXT NOT NULL DEFAULT 'SAR',
    status TEXT NOT NULL,                  -- paid, pending, failed, refunded
    invoice_date TIMESTAMP NOT NULL DEFAULT NOW(),
    payment_method TEXT                    -- Card, Bank Transfer...
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_plans_plan_type ON public.plans(plan_type);
CREATE INDEX IF NOT EXISTS idx_plans_is_active ON public.plans(is_active);

CREATE INDEX IF NOT EXISTS idx_subscriptions_user_id ON public.subscriptions(user_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_plan_id ON public.subscriptions(plan_id);
CREATE INDEX IF NOT EXISTS idx_subscriptions_status ON public.subscriptions(status);
CREATE INDEX IF NOT EXISTS idx_subscriptions_end_date ON public.subscriptions(end_date);

CREATE INDEX IF NOT EXISTS idx_usage_tracking_subscription_id ON public.usage_tracking(subscription_id);
CREATE INDEX IF NOT EXISTS idx_usage_tracking_feature ON public.usage_tracking(feature);
CREATE INDEX IF NOT EXISTS idx_usage_tracking_reset_cycle ON public.usage_tracking(reset_cycle);

CREATE INDEX IF NOT EXISTS idx_billing_subscription_id ON public.billing(subscription_id);
CREATE INDEX IF NOT EXISTS idx_billing_status ON public.billing(status);
CREATE INDEX IF NOT EXISTS idx_billing_invoice_date ON public.billing(invoice_date);

-- Insert default plans
INSERT INTO public.plans (plan_name, plan_type, price, billing_cycle, file_limit, ai_message_limit, contract_limit, report_limit, token_limit, multi_user_limit, government_integration, description) VALUES
('Free Trial', 'free', 0, 'none', 5, 10, 2, 1, 1000, 1, false, '7-day free trial with limited features'),
('Basic Monthly', 'monthly', 29.99, 'monthly', 50, 100, 10, 5, 10000, 3, false, 'Basic monthly plan for small businesses'),
('Basic Annual', 'annual', 299.99, 'yearly', 50, 100, 10, 5, 10000, 3, false, 'Basic annual plan with 2 months free'),
('Professional Monthly', 'monthly', 59.99, 'monthly', 200, 500, 50, 25, 50000, 10, true, 'Professional monthly plan with government integration'),
('Professional Annual', 'annual', 599.99, 'yearly', 200, 500, 50, 25, 50000, 10, true, 'Professional annual plan with government integration'),
('Enterprise Monthly', 'monthly', 99.99, 'monthly', 1000, 2000, 200, 100, 200000, 50, true, 'Enterprise monthly plan with unlimited features'),
('Enterprise Annual', 'annual', 999.99, 'yearly', 1000, 2000, 200, 100, 200000, 50, true, 'Enterprise annual plan with unlimited features');

-- Create function to handle new user signup with trial plan
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

-- Create trigger to automatically create profile and trial subscription when user signs up
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();

-- Grant necessary permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON public.plans TO anon, authenticated;
GRANT ALL ON public.subscriptions TO anon, authenticated;
GRANT ALL ON public.usage_tracking TO anon, authenticated;
GRANT ALL ON public.billing TO anon, authenticated;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;

-- Enable Row Level Security (RLS)
ALTER TABLE public.plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.usage_tracking ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.billing ENABLE ROW LEVEL SECURITY;

-- Create RLS policies for plans (public read access)
CREATE POLICY "Plans are viewable by everyone" ON public.plans
    FOR SELECT USING (true);

-- Create RLS policies for subscriptions
CREATE POLICY "Users can view own subscriptions" ON public.subscriptions
    FOR SELECT USING (auth.uid() = user_id);

CREATE POLICY "Users can update own subscriptions" ON public.subscriptions
    FOR UPDATE USING (auth.uid() = user_id);

-- Create RLS policies for usage_tracking
CREATE POLICY "Users can view own usage tracking" ON public.usage_tracking
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.subscriptions 
            WHERE subscription_id = usage_tracking.subscription_id 
            AND user_id = auth.uid()
        )
    );

-- Create RLS policies for billing
CREATE POLICY "Users can view own billing" ON public.billing
    FOR SELECT USING (
        EXISTS (
            SELECT 1 FROM public.subscriptions 
            WHERE subscription_id = billing.subscription_id 
            AND user_id = auth.uid()
        )
    );

-- Add comments
COMMENT ON TYPE subscription_status_enum IS 'Subscription status enumeration: active, expired, cancelled';
COMMENT ON TYPE account_type_enum IS 'Account type enumeration: personal, business';
COMMENT ON TABLE public.profiles IS 'User profiles linked to Supabase auth.users';
COMMENT ON TABLE public.plans IS 'Subscription plans with features and limits';
COMMENT ON TABLE public.subscriptions IS 'User subscriptions linked to plans';
COMMENT ON TABLE public.usage_tracking IS 'Feature usage tracking for subscriptions';
COMMENT ON TABLE public.billing IS 'Invoices and payment tracking';

-- Create function to check feature usage
CREATE OR REPLACE FUNCTION public.check_feature_usage(
    p_user_id UUID,
    p_feature TEXT
)
RETURNS BOOLEAN AS $$
DECLARE
    v_subscription_id UUID;
    v_plan_id UUID;
    v_limit INTEGER;
    v_current_usage INTEGER;
BEGIN
    -- Get active subscription
    SELECT subscription_id, plan_id INTO v_subscription_id, v_plan_id
    FROM public.subscriptions
    WHERE user_id = p_user_id 
    AND status = 'active'::subscription_status_enum
    AND (end_date IS NULL OR end_date > NOW())
    ORDER BY start_date DESC
    LIMIT 1;
    
    -- If no active subscription, return false
    IF v_subscription_id IS NULL THEN
        RETURN FALSE;
    END IF;
    
    -- Get plan limit for the feature
    CASE p_feature
        WHEN 'file_upload' THEN SELECT file_limit INTO v_limit FROM public.plans WHERE plan_id = v_plan_id;
        WHEN 'ai_chat' THEN SELECT ai_message_limit INTO v_limit FROM public.plans WHERE plan_id = v_plan_id;
        WHEN 'contract' THEN SELECT contract_limit INTO v_limit FROM public.plans WHERE plan_id = v_plan_id;
        WHEN 'report' THEN SELECT report_limit INTO v_limit FROM public.plans WHERE plan_id = v_plan_id;
        WHEN 'token' THEN SELECT token_limit INTO v_limit FROM public.plans WHERE plan_id = v_plan_id;
        WHEN 'multi_user' THEN SELECT multi_user_limit INTO v_limit FROM public.plans WHERE plan_id = v_plan_id;
        ELSE v_limit := 0;
    END CASE;
    
    -- If unlimited (0 or NULL), return true
    IF v_limit IS NULL OR v_limit = 0 THEN
        RETURN TRUE;
    END IF;
    
    -- Get current usage from usage_tracking table
    SELECT COALESCE(used_count, 0) INTO v_current_usage
    FROM public.usage_tracking
    WHERE subscription_id = v_subscription_id 
    AND feature = p_feature;
    
    -- Return true if under limit
    RETURN v_current_usage < v_limit;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

-- Create function to increment feature usage
CREATE OR REPLACE FUNCTION public.increment_feature_usage(
    p_user_id UUID,
    p_feature TEXT,
    p_amount INTEGER DEFAULT 1
)
RETURNS INTEGER AS $$
DECLARE
    v_subscription_id UUID;
    v_new_usage INTEGER;
BEGIN
    -- Get active subscription
    SELECT subscription_id INTO v_subscription_id
    FROM public.subscriptions
    WHERE user_id = p_user_id 
    AND status = 'active'::subscription_status_enum
    AND (end_date IS NULL OR end_date > NOW())
    ORDER BY start_date DESC
    LIMIT 1;
    
    -- If no active subscription, return 0
    IF v_subscription_id IS NULL THEN
        RETURN 0;
    END IF;
    
    -- Insert or update usage tracking record
    INSERT INTO public.usage_tracking (subscription_id, feature, used_count, reset_cycle)
    VALUES (v_subscription_id, p_feature, p_amount, 'monthly')
    ON CONFLICT (subscription_id, feature) 
    DO UPDATE SET 
        used_count = usage_tracking.used_count + p_amount,
        last_reset = CASE 
            WHEN usage_tracking.should_reset() THEN NOW()
            ELSE usage_tracking.last_reset
        END
    RETURNING used_count INTO v_new_usage;
    
    RETURN v_new_usage;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;
