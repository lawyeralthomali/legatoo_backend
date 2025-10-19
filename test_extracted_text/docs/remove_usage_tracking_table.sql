-- Remove usage_tracking table since we're using JSONB current_usage instead
-- Run this in Supabase SQL Editor if you want to clean up the unused table

-- WARNING: This will permanently delete the usage_tracking table and all its data
-- Only run this if you're sure you want to use JSONB current_usage approach

-- Drop the usage_tracking table
DROP TABLE IF EXISTS public.usage_tracking CASCADE;

-- Remove any references to usage_tracking in comments
-- (No actual references to remove since we're using JSONB)

-- Add comment explaining the change
COMMENT ON COLUMN public.subscriptions.current_usage IS 'Current usage tracking in JSONB format - replaces separate usage_tracking table for simplicity';

