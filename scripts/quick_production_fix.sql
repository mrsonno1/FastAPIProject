-- 프로덕션 서버 빠른 수정용 SQL
-- 이 파일을 직접 실행하거나 복사해서 사용하세요

-- 1. 현재 상태 확인
\echo '=== 현재 item_name 컬럼 상태 ==='
SELECT 
    c.column_name,
    c.is_nullable
FROM information_schema.columns c
WHERE c.table_name = 'custom_designs' 
AND c.column_name = 'item_name';

-- 2. NOT NULL 제약조건 제거
\echo '\n=== NOT NULL 제약조건 제거 중... ==='
ALTER TABLE custom_designs 
ALTER COLUMN item_name DROP NOT NULL;

-- 3. 컬럼 설명 추가
\echo '\n=== 컬럼 설명 추가 중... ==='
COMMENT ON COLUMN custom_designs.item_name IS 'Design code. Initially NULL, auto-generated when status=3';

-- 4. 변경 확인
\echo '\n=== 변경 후 상태 확인 ==='
SELECT 
    c.column_name,
    c.is_nullable
FROM information_schema.columns c
WHERE c.table_name = 'custom_designs' 
AND c.column_name = 'item_name';

\echo '\n=== 마이그레이션 완료! ==='