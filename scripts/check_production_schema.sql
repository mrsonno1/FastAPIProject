-- 프로덕션 서버 스키마 확인 스크립트

-- 1. custom_designs 테이블의 전체 구조 확인
\echo '=== custom_designs 테이블 구조 ==='
\d custom_designs

-- 2. user_id 컬럼의 정확한 타입 확인
\echo '\n=== user_id 컬럼 타입 정보 ==='
SELECT 
    column_name,
    data_type,
    character_maximum_length,
    is_nullable,
    column_default
FROM information_schema.columns
WHERE table_name = 'custom_designs'
AND column_name = 'user_id';

-- 3. account (AdminUser) 테이블의 id 타입 확인
\echo '\n=== account 테이블의 id 컬럼 타입 ==='
SELECT 
    column_name,
    data_type,
    is_nullable
FROM information_schema.columns
WHERE table_name = 'account'
AND column_name = 'id';

-- 4. 실제 데이터 샘플 확인
\echo '\n=== custom_designs 데이터 샘플 (user_id 타입 확인) ==='
SELECT 
    id,
    user_id,
    pg_typeof(user_id) as user_id_type,
    item_name,
    status
FROM custom_designs
LIMIT 5;

-- 5. 타입 불일치가 있는지 확인
\echo '\n=== 타입 캐스팅 테스트 ==='
SELECT COUNT(*) 
FROM custom_designs 
WHERE user_id::text = '12';  -- 문자열로 캐스팅 테스트

SELECT COUNT(*) 
FROM custom_designs 
WHERE user_id = 12;  -- 정수로 직접 비교