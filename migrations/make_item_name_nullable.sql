-- Migration: Make item_name nullable in custom_designs table
-- Date: 2025-08-04
-- Description: Allow item_name to be NULL initially, will be set when status becomes 3

-- Make item_name column nullable
ALTER TABLE custom_designs 
ALTER COLUMN item_name DROP NOT NULL;

-- Add comment to explain the business logic
COMMENT ON COLUMN custom_designs.item_name IS 'Design code. Initially NULL, auto-generated as {account_code}-{sequence} when status becomes 3 (completed)';