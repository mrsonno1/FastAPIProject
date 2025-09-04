-- =====================================================
-- 삭제된 계정의 username/account_code 재사용 활성화
-- Partial Unique Index를 사용하여 is_deleted=false인 경우에만 unique 제약 적용
-- =====================================================

-- 1. 기존 UNIQUE 제약조건 제거
-- 영문 제약조건
ALTER TABLE account DROP CONSTRAINT IF EXISTS account_username_key;
ALTER TABLE account DROP CONSTRAINT IF EXISTS account_account_code_key;

-- 한글 제약조건 (이전에 생성된 경우)
ALTER TABLE account DROP CONSTRAINT IF EXISTS "관리자계정_아이디_key";
ALTER TABLE account DROP CONSTRAINT IF EXISTS "관리자계정_계정코드_key";

-- 2. 기존 unique 인덱스 제거 (있는 경우)
DROP INDEX IF EXISTS account_username_key;
DROP INDEX IF EXISTS account_account_code_key;

-- 3. Partial Unique Index 생성
-- is_deleted가 false인 레코드에 대해서만 username이 unique하도록 설정
CREATE UNIQUE INDEX IF NOT EXISTS account_username_active_unique 
ON account(username) 
WHERE is_deleted = false;

-- is_deleted가 false이고 account_code가 NULL이 아닌 경우에만 account_code가 unique하도록 설정
CREATE UNIQUE INDEX IF NOT EXISTS account_account_code_active_unique 
ON account(account_code) 
WHERE is_deleted = false AND account_code IS NOT NULL;

-- 4. 검색 성능을 위한 일반 인덱스 추가 (선택사항)
CREATE INDEX IF NOT EXISTS idx_account_username ON account(username);
CREATE INDEX IF NOT EXISTS idx_account_is_deleted ON account(is_deleted);

-- 5. 변경 확인 쿼리
-- 인덱스 목록 확인
SELECT 
    indexname,
    CASE 
        WHEN indexdef LIKE '%WHERE%' THEN 'Partial Index'
        ELSE 'Regular Index'
    END as index_type,
    indexdef
FROM pg_indexes 
WHERE tablename = 'account'
AND (indexname LIKE '%username%' OR indexname LIKE '%account_code%')
ORDER BY indexname;

-- 제약조건 확인 (UNIQUE 제약이 없어야 함)
SELECT 
    conname AS constraint_name,
    CASE contype 
        WHEN 'u' THEN 'UNIQUE'
        WHEN 'p' THEN 'PRIMARY KEY'
        WHEN 'f' THEN 'FOREIGN KEY'
        ELSE contype
    END AS constraint_type
FROM pg_constraint 
WHERE conrelid = 'account'::regclass
AND contype = 'u';

-- 6. 테스트 쿼리 (선택사항)
-- 삭제된 계정과 활성 계정에 동일한 username 사용 가능 여부 테스트
/*
-- 테스트 데이터 삽입
INSERT INTO account (username, hashed_password, permission, company_name, is_deleted)
VALUES ('reuse_test', 'dummy_hash', 'viewer', 'Test Company', true);

INSERT INTO account (username, hashed_password, permission, company_name, is_deleted)
VALUES ('reuse_test', 'dummy_hash', 'viewer', 'Test Company', false);

-- 확인
SELECT username, is_deleted FROM account WHERE username = 'reuse_test';

-- 테스트 데이터 정리
DELETE FROM account WHERE username = 'reuse_test';
*/

-- =====================================================
-- 적용 완료 후 예상 동작
-- =====================================================
-- 1. 활성 계정(is_deleted=false) 간에는 username/account_code 중복 불가
-- 2. 삭제된 계정(is_deleted=true)의 username/account_code는 새 활성 계정에서 재사용 가능
-- 3. 여러 개의 삭제된 계정이 동일한 username/account_code 가질 수 있음
-- 4. 검색 성능은 일반 인덱스로 유지됨