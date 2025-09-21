-- =====================================================
-- Migration Script: Old to New Subscription System
-- Run this in Supabase SQL Editor after setting up new tables
-- =====================================================

-- Step 1: Create the new tables (run database_setup_new.sql first)
-- This script assumes the new tables are already created

-- Step 2: Migrate existing user_subscriptions to new subscriptions table
INSERT INTO public.subscriptions (
    user_id,
    plan_id,
    start_date,
    end_date,
    status,
    current_usage
)
SELECT 
    us.user_id,
    CASE 
        WHEN us.plan_type = 'trial' THEN (
            SELECT plan_id FROM public.plans 
            WHERE plan_type = 'free' AND is_active = true 
            LIMIT 1
        )
        WHEN us.plan_type = 'paid' THEN (
            SELECT plan_id FROM public.plans 
            WHERE plan_type = 'monthly' AND is_active = true 
            LIMIT 1
        )
    END as plan_id,
    us.start_date,
    us.end_date,
    CASE 
        WHEN us.is_active = false THEN 'cancelled'
        WHEN us.end_date < NOW() THEN 'expired'
        ELSE 'active'
    END as status,
    '{}' as current_usage
FROM user_subscriptions us
WHERE EXISTS (
    SELECT 1 FROM public.plans 
    WHERE plan_type = CASE 
        WHEN us.plan_type = 'trial' THEN 'free'
        WHEN us.plan_type = 'paid' THEN 'monthly'
    END
);

-- Step 3: Create usage tracking records for existing subscriptions
INSERT INTO public.usage_tracking (
    subscription_id,
    feature,
    used_count,
    reset_cycle
)
SELECT 
    s.subscription_id,
    'file_upload',
    0,
    'monthly'
FROM public.subscriptions s
WHERE s.status = 'active';

INSERT INTO public.usage_tracking (
    subscription_id,
    feature,
    used_count,
    reset_cycle
)
SELECT 
    s.subscription_id,
    'ai_chat',
    0,
    'monthly'
FROM public.subscriptions s
WHERE s.status = 'active';

INSERT INTO public.usage_tracking (
    subscription_id,
    feature,
    used_count,
    reset_cycle
)
SELECT 
    s.subscription_id,
    'contract',
    0,
    'monthly'
FROM public.subscriptions s
WHERE s.status = 'active';

INSERT INTO public.usage_tracking (
    subscription_id,
    feature,
    used_count,
    reset_cycle
)
SELECT 
    s.subscription_id,
    'report',
    0,
    'monthly'
FROM public.subscriptions s
WHERE s.status = 'active';

INSERT INTO public.usage_tracking (
    subscription_id,
    feature,
    used_count,
    reset_cycle
)
SELECT 
    s.subscription_id,
    'token',
    0,
    'monthly'
FROM public.subscriptions s
WHERE s.status = 'active';

INSERT INTO public.usage_tracking (
    subscription_id,
    feature,
    used_count,
    reset_cycle
)
SELECT 
    s.subscription_id,
    'multi_user',
    0,
    'monthly'
FROM public.subscriptions s
WHERE s.status = 'active';

-- Step 4: Create sample billing records for paid subscriptions
INSERT INTO public.billing (
    subscription_id,
    amount,
    currency,
    status,
    payment_method
)
SELECT 
    s.subscription_id,
    p.price,
    'SAR',
    'paid',
    'Card'
FROM public.subscriptions s
JOIN public.plans p ON s.plan_id = p.plan_id
WHERE s.status = 'active' 
AND p.plan_type != 'free'
AND s.start_date < NOW() - INTERVAL '1 day';

-- Step 5: Verify migration results
SELECT 
    'Migration Summary' as step,
    COUNT(*) as total_subscriptions,
    COUNT(CASE WHEN status = 'active' THEN 1 END) as active_subscriptions,
    COUNT(CASE WHEN status = 'expired' THEN 1 END) as expired_subscriptions,
    COUNT(CASE WHEN status = 'cancelled' THEN 1 END) as cancelled_subscriptions
FROM public.subscriptions;

SELECT 
    'Plan Distribution' as step,
    p.plan_name,
    COUNT(s.subscription_id) as subscription_count
FROM public.plans p
LEFT JOIN public.subscriptions s ON p.plan_id = s.plan_id
GROUP BY p.plan_name, p.plan_type
ORDER BY p.price;

SELECT 
    'Usage Tracking Setup' as step,
    COUNT(*) as total_usage_records,
    COUNT(DISTINCT subscription_id) as subscriptions_with_tracking
FROM public.usage_tracking;

SELECT 
    'Billing Records' as step,
    COUNT(*) as total_invoices,
    COUNT(CASE WHEN status = 'paid' THEN 1 END) as paid_invoices,
    SUM(amount) as total_revenue
FROM public.billing;

-- Step 6: Optional - Drop old tables after verification
-- Uncomment these lines after verifying the migration worked correctly

/*
-- Drop old user_subscriptions table
DROP TABLE IF EXISTS public.user_subscriptions;

-- Update the handle_new_user function to use new system
-- (This is already done in database_setup_new.sql)
*/

-- =====================================================
-- Migration Complete!
-- =====================================================

/*
Next steps:
1. Update your FastAPI application to use the new models and services
2. Test the new subscription system
3. Update your frontend to work with the new API endpoints
4. After thorough testing, drop the old user_subscriptions table
*/
