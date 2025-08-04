-- AdminUser 테이블에 is_deleted 컬럼 추가
-- account 테이블이 실제 테이블명입니다 (AdminUser 모델이 account 테이블을 사용)

ALTER TABLE account ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE NOT NULL;

-- 기존 데이터에 대해 is_deleted = FALSE 확인
UPDATE account SET is_deleted = FALSE WHERE is_deleted IS NULL;