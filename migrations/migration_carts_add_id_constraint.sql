-- =============================================================================
-- Migration: Add transitional check constraint to carts
-- Description: Add an "at most one" CHECK constraint for (portfolio_id, custom_design_id)
--              without reapplying already executed steps (columns, FKs, indexes).
-- Date: 2025-10-27
-- =============================================================================

-- Optional: drop any previous attempt with old name (safe if not present)
ALTER TABLE public.carts DROP CONSTRAINT IF EXISTS chk_carts_exclusive_id;
ALTER TABLE public.carts DROP CONSTRAINT IF EXISTS chk_carts_id_at_most_one;

-- Transitional constraint: at most one of the two IDs can be non-null.
-- This allows both NULL during migration/backfill, but prevents both being set.
-- Use NOT VALID to avoid immediate full-table validation; validate afterwards.
ALTER TABLE public.carts
    ADD CONSTRAINT chk_carts_id_at_most_one
    CHECK (
        portfolio_id IS NULL OR custom_design_id IS NULL
    ) NOT VALID;

-- Optionally validate now (will fail if any row has both IDs set)
-- Comment this line out if you prefer to validate later after backfill.
ALTER TABLE public.carts VALIDATE CONSTRAINT chk_carts_id_at_most_one;

-- Notes:
-- - Columns portfolio_id, custom_design_id and FKs/Indexes were created previously.
-- - After backfill and client migration, you may tighten to exact-one (XOR):
--   ALTER TABLE public.carts
--       ADD CONSTRAINT chk_carts_id_exactly_one
--       CHECK ((portfolio_id IS NOT NULL) <> (custom_design_id IS NOT NULL)) NOT VALID;
--   -- Later:
--   ALTER TABLE public.carts VALIDATE CONSTRAINT chk_carts_id_exactly_one;
