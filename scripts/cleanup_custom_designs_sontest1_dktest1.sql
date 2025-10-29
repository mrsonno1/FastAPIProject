-- 목적: user_id 가 'sontest1', 'dktest1' 인 custom_designs 데이터를 백업 후 삭제
--       progressstatus 의 외래키(custom_design_id) 참조는 NULL 로 해제하여 기록 유지
-- DB: PostgreSQL

BEGIN;

-- 0) 대상 id를 임시 테이블로 확정 (WITH CTE는 문장 간 공유되지 않으므로 TEMP 테이블 사용)
CREATE TEMP TABLE tmp_target_custom_designs AS
SELECT id
FROM custom_designs
WHERE user_id IN ('sontest1', 'dktest1');

-- 1) custom_designs 백업(누적, 중복 방지)
CREATE TABLE IF NOT EXISTS custom_designs_backup (LIKE custom_designs INCLUDING ALL);

INSERT INTO custom_designs_backup
SELECT cd.*
FROM custom_designs cd
JOIN tmp_target_custom_designs t ON t.id = cd.id
WHERE NOT EXISTS (
  SELECT 1 FROM custom_designs_backup b WHERE b.id = cd.id
);

-- 2) progressstatus 백업(누적, 중복 방지)
CREATE TABLE IF NOT EXISTS progressstatus_backup (LIKE progressstatus INCLUDING ALL);

INSERT INTO progressstatus_backup
SELECT p.*
FROM progressstatus p
WHERE p.custom_design_id IN (SELECT id FROM tmp_target_custom_designs)
  AND NOT EXISTS (
    SELECT 1 FROM progressstatus_backup b WHERE b.id = p.id
  );

-- 3) 참조 해제(progressstatus → custom_designs)
UPDATE progressstatus
SET custom_design_id = NULL
WHERE custom_design_id IN (SELECT id FROM tmp_target_custom_designs);

-- 4) 원본 삭제(custom_designs)
DELETE FROM custom_designs
WHERE id IN (SELECT id FROM tmp_target_custom_designs);

COMMIT;

-- 검증(옵션)
-- SELECT COUNT(*) AS remaining_custom_designs
-- FROM custom_designs
-- WHERE user_id IN ('sontest1','dktest1');
--
-- SELECT COUNT(*) AS dangling_refs
-- FROM progressstatus
-- WHERE custom_design_id IN (
--   SELECT id FROM custom_designs_backup
--   WHERE user_id IN ('sontest1','dktest1')
-- );
