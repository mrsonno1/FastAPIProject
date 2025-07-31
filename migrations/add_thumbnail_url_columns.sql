-- Migration: Add thumbnail_url columns to tables
-- Date: 2025-07-31
-- Description: Add thumbnail_url column to images, brands, custom_designs, and portfolios tables

-- Add thumbnail_url to images table
ALTER TABLE images 
ADD COLUMN IF NOT EXISTS thumbnail_url VARCHAR(500);

-- Add thumbnail_url to brands table
ALTER TABLE brands 
ADD COLUMN IF NOT EXISTS thumbnail_url VARCHAR(500);

-- Add thumbnail_url to custom_designs table
ALTER TABLE custom_designs 
ADD COLUMN IF NOT EXISTS thumbnail_url VARCHAR(500);

-- Add thumbnail_url to portfolios table
ALTER TABLE portfolios 
ADD COLUMN IF NOT EXISTS thumbnail_url VARCHAR(500);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_images_thumbnail_url ON images(thumbnail_url);
CREATE INDEX IF NOT EXISTS idx_brands_thumbnail_url ON brands(thumbnail_url);
CREATE INDEX IF NOT EXISTS idx_custom_designs_thumbnail_url ON custom_designs(thumbnail_url);
CREATE INDEX IF NOT EXISTS idx_portfolios_thumbnail_url ON portfolios(thumbnail_url);

-- Optional: Generate thumbnails for existing images (run as separate script)
-- This is a placeholder comment for a separate Python script that would:
-- 1. Query all existing images/brands/designs/portfolios
-- 2. Generate thumbnails for each
-- 3. Update the thumbnail_url column