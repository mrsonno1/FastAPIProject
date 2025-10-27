-- Make color_name nullable and remove unique constraint
-- This allows empty strings and null values for color names

-- Remove unique constraint on color_name
ALTER TABLE colors DROP CONSTRAINT IF EXISTS colors_color_name_key;

-- Make color_name nullable
ALTER TABLE colors ALTER COLUMN color_name DROP NOT NULL;

-- Add comment
COMMENT ON COLUMN colors.color_name IS '컬러 이름 (빈 문자열 및 NULL 허용)';