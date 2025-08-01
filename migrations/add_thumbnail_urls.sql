-- Add thumbnail_url column to releasedproducts table
ALTER TABLE releasedproducts 
ADD COLUMN IF NOT EXISTS thumbnail_url VARCHAR;

-- You may also want to add thumbnail_url to other tables if they don't exist yet:
-- ALTER TABLE portfolios ADD COLUMN IF NOT EXISTS thumbnail_url VARCHAR;
-- ALTER TABLE brands ADD COLUMN IF NOT EXISTS thumbnail_url VARCHAR;
-- ALTER TABLE images ADD COLUMN IF NOT EXISTS thumbnail_url VARCHAR;
-- ALTER TABLE custom_designs ADD COLUMN IF NOT EXISTS thumbnail_url VARCHAR;