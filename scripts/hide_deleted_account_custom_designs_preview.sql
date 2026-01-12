-- Preview rows that would be hidden by hide_deleted_account_custom_designs.sql.
-- Target DB: PostgreSQL

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

-- Preview 1: designs created before the current active account was created.
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
SELECT
    cd.id,
    cd.user_id,
    cd.status,
    cd.created_at,
    aa.created_at AS active_account_created_at
FROM custom_designs AS cd
JOIN active_accounts AS aa ON aa.username = cd.user_id
JOIN deleted_usernames AS du ON du.username = aa.username
WHERE cd.created_at < aa.created_at
  AND cd.status != '99'
ORDER BY cd.user_id, cd.created_at;

-- Preview 2: designs that still reference deleted numeric account ids.
SELECT
    cd.id,
    cd.user_id,
    cd.status,
    cd.created_at
FROM custom_designs AS cd
WHERE cd.user_id IN (
    SELECT id::text
    FROM account
    WHERE is_deleted = true
)
  AND cd.status != '99'
ORDER BY cd.user_id, cd.created_at;
