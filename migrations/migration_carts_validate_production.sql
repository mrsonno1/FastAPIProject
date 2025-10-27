-- =============================================================================
-- Production Validation: Validate NOT VALID constraints and (optionally) enforce XOR
-- Description:
--   - Validate existing NOT VALID constraints to fully enforce them.
--   - Optionally move from at-most-one to exactly-one and drop the transitional check.
-- Date: 2025-10-27
-- =============================================================================

SET lock_timeout = '5s';
SET statement_timeout = '15min';

-- 1) Validate existing NOT VALID constraints (FKs and check)
DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_constraint c JOIN pg_class t ON t.oid = c.conrelid
    WHERE c.conname = 'fk_carts_portfolio' AND t.relname = 'carts' AND NOT c.convalidated
  ) THEN
    ALTER TABLE public.carts VALIDATE CONSTRAINT fk_carts_portfolio;
  END IF;
END$$;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_constraint c JOIN pg_class t ON t.oid = c.conrelid
    WHERE c.conname = 'fk_carts_custom_design' AND t.relname = 'carts' AND NOT c.convalidated
  ) THEN
    ALTER TABLE public.carts VALIDATE CONSTRAINT fk_carts_custom_design;
  END IF;
END$$;

DO $$
BEGIN
  IF EXISTS (
    SELECT 1 FROM pg_constraint c JOIN pg_class t ON t.oid = c.conrelid
    WHERE c.conname = 'chk_carts_id_at_most_one' AND t.relname = 'carts' AND NOT c.convalidated
  ) THEN
    ALTER TABLE public.carts VALIDATE CONSTRAINT chk_carts_id_at_most_one;
  END IF;
END$$;

-- 2) Optional: Enforce exactly one non-null (XOR) after full backfill
--    Adds strict constraint as NOT VALID, validates it, then drops transitional.
-- DO $$
-- BEGIN
--   IF NOT EXISTS (
--     SELECT 1 FROM pg_constraint c JOIN pg_class t ON t.oid = c.conrelid
--     WHERE c.conname = 'chk_carts_id_exactly_one' AND t.relname = 'carts'
--   ) THEN
--     ALTER TABLE public.carts
--       ADD CONSTRAINT chk_carts_id_exactly_one
--       CHECK ((portfolio_id IS NOT NULL) <> (custom_design_id IS NOT NULL)) NOT VALID;
--   END IF;
-- END$$;
--
-- ALTER TABLE public.carts VALIDATE CONSTRAINT chk_carts_id_exactly_one;
-- ALTER TABLE public.carts DROP CONSTRAINT IF EXISTS chk_carts_id_at_most_one;

