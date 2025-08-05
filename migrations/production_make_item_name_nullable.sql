-- Production Migration: Make item_name nullable in custom_designs table
-- Server: 13.125.43.42
-- Date: 2025-08-05
-- Description: Allow item_name to be NULL initially, will be set when status becomes 3

-- IMPORTANT: Run this on production database
-- Make sure to backup the database before running this migration

-- Check current constraint status before migration
SELECT 
    c.column_name,
    c.is_nullable,
    c.column_default
FROM information_schema.columns c
WHERE c.table_name = 'custom_designs' 
AND c.column_name = 'item_name';

-- Make item_name column nullable
ALTER TABLE custom_designs 
ALTER COLUMN item_name DROP NOT NULL;

-- Add comment to explain the business logic
COMMENT ON COLUMN custom_designs.item_name IS 'Design code. Initially NULL, auto-generated as sequence number (0001, 0002, ...) when status becomes 3 (completed)';

-- Verify the change after migration
SELECT 
    c.column_name,
    c.is_nullable,
    c.column_default
FROM information_schema.columns c
WHERE c.table_name = 'custom_designs' 
AND c.column_name = 'item_name';