-- Hide legacy custom designs tied to deleted accounts or reused usernames.
-- Target DB: PostgreSQL

BEGIN;

-- Sanity check: usernames that have both active and deleted rows.
SELECT
    username,
    COUNT(*) FILTER (WHERE is_deleted = false) AS active_count,
    COUNT(*) FILTER (WHERE is_deleted = true) AS deleted_count
FROM account
GROUP BY username
HAVING COUNT(*) FILTER (WHERE is_deleted = false) > 0
   AND COUNT(*) FILTER (WHERE is_deleted = true) > 0
ORDER BY username;

-- Update 1: hide designs created before the current active account was created.
WITH active_accounts AS (
    SELECT username, created_at
    FROM account
    WHERE is_deleted = false
),
deleted_usernames AS (
    SELECT DISTINCT username
    FROM account
    WHERE is_deleted = true
)
UPDATE custom_designs AS cd
SET status = '99'
FROM active_accounts AS aa
JOIN deleted_usernames AS du ON du.username = aa.username
WHERE cd.user_id = aa.username
  AND cd.created_at < aa.created_at
  AND cd.status != '99';

-- Update 2: hide designs that still reference deleted numeric account ids.
UPDATE custom_designs
SET status = '99'
WHERE user_id IN (
    SELECT id::text
    FROM account
    WHERE is_deleted = true
)
  AND status != '99';

-- Optional verification: count remaining visible designs for reused usernames.
WITH active_accounts AS (
    SELECT username
    FROM account
    WHERE is_deleted = false
),
deleted_usernames AS (
    SELECT DISTINCT username
    FROM account
    WHERE is_deleted = true
)
SELECT cd.user_id, COUNT(*) AS visible_designs
FROM custom_designs AS cd
JOIN active_accounts AS aa ON aa.username = cd.user_id
JOIN deleted_usernames AS du ON du.username = aa.username
WHERE cd.status != '99'
GROUP BY cd.user_id
ORDER BY cd.user_id;

COMMIT;
