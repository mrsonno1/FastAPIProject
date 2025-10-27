-- ============================================================================
-- Migration: Add portfolio_id and custom_design_id to Cart Table
-- Description: Cart 테이블에 ID 컬럼 추가하여 정확한 참조 가능하도록 개선
-- Date: 2025-10-21
-- Priority: HIGH - 중복 design_name 문제 해결을 위해 필요
-- ============================================================================

-- Step 1: Add new columns
ALTER TABLE cart ADD COLUMN portfolio_id INTEGER NULL;
ALTER TABLE cart ADD COLUMN custom_design_id INTEGER NULL;

-- Step 2: Add foreign key constraints
ALTER TABLE cart
    ADD CONSTRAINT fk_cart_portfolio
    FOREIGN KEY (portfolio_id)
    REFERENCES portfolios(id)
    ON DELETE SET NULL;

ALTER TABLE cart
    ADD CONSTRAINT fk_cart_custom_design
    FOREIGN KEY (custom_design_id)
    REFERENCES custom_design(id)
    ON DELETE SET NULL;

-- Step 3: Add check constraint (둘 중 하나만 NULL이 아니어야 함)
ALTER TABLE cart
    ADD CONSTRAINT chk_cart_exclusive_id
    CHECK (
        (portfolio_id IS NOT NULL AND custom_design_id IS NULL) OR
        (portfolio_id IS NULL AND custom_design_id IS NOT NULL)
    );

-- Step 4: Create indexes for performance
CREATE INDEX idx_cart_portfolio_id ON cart(portfolio_id) WHERE portfolio_id IS NOT NULL;
CREATE INDEX idx_cart_custom_design_id ON cart(custom_design_id) WHERE custom_design_id IS NOT NULL;

-- Step 5: Verify the migration
-- Run this to check:
-- SELECT column_name, is_nullable, data_type
-- FROM information_schema.columns
-- WHERE table_name = 'cart' AND column_name IN ('portfolio_id', 'custom_design_id');

-- ============================================================================
-- Migration Notes:
--
-- 1. 기존 데이터 처리:
--    - 기존 cart 레코드는 portfolio_id, custom_design_id가 NULL
--    - 이는 정상입니다 (item_name으로 조회 계속 사용)
--    - 새로운 데이터만 ID 컬럼에 값 저장됨
--
-- 2. 애플리케이션 코드 변경 필요:
--    - add_to_cart() 함수에서 ID 저장 로직 추가
--    - get_cart_items() 함수에서 ID 우선 조회 로직 추가
--
-- 3. 롤백 방법 (필요시):
--    DROP INDEX idx_cart_custom_design_id;
--    DROP INDEX idx_cart_portfolio_id;
--    ALTER TABLE cart DROP CONSTRAINT chk_cart_exclusive_id;
--    ALTER TABLE cart DROP CONSTRAINT fk_cart_custom_design;
--    ALTER TABLE cart DROP CONSTRAINT fk_cart_portfolio;
--    ALTER TABLE cart DROP COLUMN custom_design_id;
--    ALTER TABLE cart DROP COLUMN portfolio_id;
-- ============================================================================
