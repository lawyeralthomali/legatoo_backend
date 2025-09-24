-- Add missing foreign key constraints to match SQLAlchemy models
-- Run this in Supabase SQL Editor

-- Add foreign key constraint for usage_tracking.subscription_id
ALTER TABLE public.usage_tracking 
ADD CONSTRAINT usage_tracking_subscription_id_fkey 
FOREIGN KEY (subscription_id) REFERENCES public.subscriptions(subscription_id) ON DELETE CASCADE;

-- Add foreign key constraint for billing.subscription_id
ALTER TABLE public.billing 
ADD CONSTRAINT billing_subscription_id_fkey 
FOREIGN KEY (subscription_id) REFERENCES public.subscriptions(subscription_id) ON DELETE CASCADE;

-- Verify the constraints were added
SELECT 
    tc.table_name, 
    tc.constraint_name, 
    tc.constraint_type,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name 
FROM 
    information_schema.table_constraints AS tc 
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
      AND tc.table_schema = kcu.table_schema
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
      AND ccu.table_schema = tc.table_schema
WHERE tc.constraint_type = 'FOREIGN KEY' 
  AND tc.table_schema = 'public'
  AND tc.table_name IN ('subscriptions', 'usage_tracking', 'billing')
ORDER BY tc.table_name, tc.constraint_name;

