-- custom_designs: user_id가 'test'로 시작하는 데이터 백업 후 삭제
-- DB: PostgreSQL
-- 참고: 필요 시 'test%'를 다른 접두로 변경하여 사용하세요.

BEGIN;

-- 1) 백업 테이블 생성(없으면 생성) - 원본 스키마/제약/인덱스 포함
CREATE TABLE IF NOT EXISTS custom_designs_backup (LIKE custom_designs INCLUDING ALL);

-- 2) 백업: 중복 삽입 방지(id 기준)
INSERT INTO custom_designs_backup
SELECT cd.*
FROM custom_designs cd
WHERE cd.user_id ILIKE 'test%'
  AND NOT EXISTS (
    SELECT 1 FROM custom_designs_backup b WHERE b.id = cd.id
  );

-- 3) 삭제: user_id가 'test'로 시작하는 데이터 제거
DELETE FROM custom_designs
WHERE user_id ILIKE 'test%';

COMMIT;

-- 4) 검증(옵션)
-- 남은 건수(0이어야 정상)
-- SELECT COUNT(*) AS remaining FROM custom_designs WHERE user_id ILIKE 'test%';
-- 백업 건수 확인
-- SELECT COUNT(*) AS backed_up FROM custom_designs_backup WHERE user_id ILIKE 'test%';

