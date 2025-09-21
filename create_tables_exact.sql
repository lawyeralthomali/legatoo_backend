-- =====================================================
-- Exact Table Structure as Requested
-- Run this in Supabase SQL Editor
-- =====================================================

-- Create plans table
CREATE TABLE public.plans (
  plan_id uuid primary key default extensions.uuid_generate_v4(),
  plan_name text not null,               -- Free Trial, Monthly, Annual
  plan_type text not null,               -- free, monthly, annual
  price numeric(10,2) not null default 0, -- السعر (0 للـ Free)
  billing_cycle text not null,           -- monthly / yearly / none
  file_limit int,                        -- عدد الملفات المسموح
  ai_message_limit int,                  -- عدد الرسائل
  contract_limit int,                    -- عدد العقود
  report_limit int,                      -- عدد التقارير القابلة للتصدير
  token_limit int,                       -- حد التوكنات
  multi_user_limit int,                  -- عدد المستخدمين المسموح
  government_integration boolean default false,
  description text,
  is_active boolean not null default true
);

-- Create subscriptions table
CREATE TABLE public.subscriptions (
  subscription_id uuid primary key default extensions.uuid_generate_v4(),
  user_id uuid references public.profiles(id) on delete cascade,
  plan_id uuid references public.plans(plan_id) on delete restrict,
  start_date timestamp not null default now(),
  end_date timestamp,                    -- تاريخ انتهاء الاشتراك
  auto_renew boolean default true,
  status text not null default 'active',  -- active, expired, cancelled
  current_usage jsonb default '{}'        -- تخزين الاستخدام الحالي بصيغة JSON
);

-- Create usage_tracking table
CREATE TABLE public.usage_tracking (
  usage_id uuid primary key default extensions.uuid_generate_v4(),
  subscription_id uuid references public.subscriptions(subscription_id) on delete cascade,
  feature text not null,                 -- file_upload, ai_chat, contract, token
  used_count int not null default 0,
  reset_cycle text not null,             -- daily / monthly / yearly
  last_reset timestamp default now()
);

-- Create billing table
CREATE TABLE public.billing (
  invoice_id uuid primary key default extensions.uuid_generate_v4(),
  subscription_id uuid references public.subscriptions(subscription_id) on delete cascade,
  amount numeric(10,2) not null,
  currency text not null default 'SAR',
  status text not null,                  -- paid, pending, failed, refunded
  invoice_date timestamp not null default now(),
  payment_method text                    -- Card, Bank Transfer...
);

-- Insert default plans
INSERT INTO public.plans (plan_name, plan_type, price, billing_cycle, file_limit, ai_message_limit, contract_limit, report_limit, token_limit, multi_user_limit, government_integration, description) VALUES
('Free Trial', 'free', 0, 'none', 5, 10, 2, 1, 1000, 1, false, '7-day free trial with limited features'),
('Basic Monthly', 'monthly', 29.99, 'monthly', 50, 100, 10, 5, 10000, 3, false, 'Basic monthly plan for small businesses'),
('Basic Annual', 'annual', 299.99, 'yearly', 50, 100, 10, 5, 10000, 3, false, 'Basic annual plan with 2 months free'),
('Professional Monthly', 'monthly', 59.99, 'monthly', 200, 500, 50, 25, 50000, 10, true, 'Professional monthly plan with government integration'),
('Professional Annual', 'annual', 599.99, 'yearly', 200, 500, 50, 25, 50000, 10, true, 'Professional annual plan with government integration'),
('Enterprise Monthly', 'monthly', 99.99, 'monthly', 1000, 2000, 200, 100, 200000, 50, true, 'Enterprise monthly plan with unlimited features'),
('Enterprise Annual', 'annual', 999.99, 'yearly', 1000, 2000, 200, 100, 200000, 50, true, 'Enterprise annual plan with unlimited features');

-- Create indexes for better performance
CREATE INDEX idx_plans_plan_type ON public.plans(plan_type);
CREATE INDEX idx_plans_is_active ON public.plans(is_active);
CREATE INDEX idx_subscriptions_user_id ON public.subscriptions(user_id);
CREATE INDEX idx_subscriptions_plan_id ON public.subscriptions(plan_id);
CREATE INDEX idx_subscriptions_status ON public.subscriptions(status);
CREATE INDEX idx_usage_tracking_subscription_id ON public.usage_tracking(subscription_id);
CREATE INDEX idx_usage_tracking_feature ON public.usage_tracking(feature);
CREATE INDEX idx_billing_subscription_id ON public.billing(subscription_id);
CREATE INDEX idx_billing_status ON public.billing(status);

-- Enable Row Level Security
ALTER TABLE public.plans ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subscriptions ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.usage_tracking ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.billing ENABLE ROW LEVEL SECURITY;

-- Create RLS policies
CREATE POLICY "Plans are viewable by everyone" ON public.plans FOR SELECT USING (true);
CREATE POLICY "Users can view own subscriptions" ON public.subscriptions FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can view own usage tracking" ON public.usage_tracking FOR SELECT USING (
    EXISTS (SELECT 1 FROM public.subscriptions WHERE subscription_id = usage_tracking.subscription_id AND user_id = auth.uid())
);
CREATE POLICY "Users can view own billing" ON public.billing FOR SELECT USING (
    EXISTS (SELECT 1 FROM public.subscriptions WHERE subscription_id = billing.subscription_id AND user_id = auth.uid())
);

-- Grant permissions
GRANT USAGE ON SCHEMA public TO anon, authenticated;
GRANT ALL ON public.plans TO anon, authenticated;
GRANT ALL ON public.subscriptions TO anon, authenticated;
GRANT ALL ON public.usage_tracking TO anon, authenticated;
GRANT ALL ON public.billing TO anon, authenticated;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO anon, authenticated;

-- Update handle_new_user function to create trial subscription
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

-- Create trigger
DROP TRIGGER IF EXISTS on_auth_user_created ON auth.users;
CREATE TRIGGER on_auth_user_created
    AFTER INSERT ON auth.users
    FOR EACH ROW EXECUTE FUNCTION public.handle_new_user();
