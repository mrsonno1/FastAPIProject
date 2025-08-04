-- countries 테이블에 영문 이름 컬럼 추가 및 데이터 업데이트
-- PostgreSQL 용

-- 1. country_name_en 컬럼 추가
ALTER TABLE countries 
ADD COLUMN IF NOT EXISTS country_name_en VARCHAR(255);

-- 2. 인덱스 추가 (검색 성능 향상)
CREATE INDEX IF NOT EXISTS idx_countries_country_name_en 
ON countries(country_name_en);

/*
-- 3. 기본 영문 국가명 데이터 업데이트
-- 자주 사용되는 국가들의 영문명을 미리 설정
UPDATE countries SET country_name_en = 'South Korea' WHERE country_name = '한국';
UPDATE countries SET country_name_en = 'United States' WHERE country_name = '미국';
UPDATE countries SET country_name_en = 'Japan' WHERE country_name = '일본';
UPDATE countries SET country_name_en = 'China' WHERE country_name = '중국';
UPDATE countries SET country_name_en = 'United Kingdom' WHERE country_name = '영국';
UPDATE countries SET country_name_en = 'Germany' WHERE country_name = '독일';
UPDATE countries SET country_name_en = 'France' WHERE country_name = '프랑스';
UPDATE countries SET country_name_en = 'Italy' WHERE country_name = '이탈리아';
UPDATE countries SET country_name_en = 'Spain' WHERE country_name = '스페인';
UPDATE countries SET country_name_en = 'Canada' WHERE country_name = '캐나다';
UPDATE countries SET country_name_en = 'Australia' WHERE country_name = '호주';
UPDATE countries SET country_name_en = 'Netherlands' WHERE country_name = '네덜란드';
UPDATE countries SET country_name_en = 'Brazil' WHERE country_name = '브라질';
UPDATE countries SET country_name_en = 'Russia' WHERE country_name = '러시아';
UPDATE countries SET country_name_en = 'India' WHERE country_name = '인도';
UPDATE countries SET country_name_en = 'Mexico' WHERE country_name = '멕시코';
UPDATE countries SET country_name_en = 'Singapore' WHERE country_name = '싱가포르';
UPDATE countries SET country_name_en = 'Hong Kong' WHERE country_name = '홍콩';
UPDATE countries SET country_name_en = 'Taiwan' WHERE country_name = '대만';
UPDATE countries SET country_name_en = 'Thailand' WHERE country_name = '태국';
UPDATE countries SET country_name_en = 'Vietnam' WHERE country_name = '베트남';
UPDATE countries SET country_name_en = 'Philippines' WHERE country_name = '필리핀';
UPDATE countries SET country_name_en = 'Indonesia' WHERE country_name = '인도네시아';
UPDATE countries SET country_name_en = 'Malaysia' WHERE country_name = '말레이시아';
UPDATE countries SET country_name_en = 'Switzerland' WHERE country_name = '스위스';
UPDATE countries SET country_name_en = 'Sweden' WHERE country_name = '스웨덴';
UPDATE countries SET country_name_en = 'Norway' WHERE country_name = '노르웨이';
UPDATE countries SET country_name_en = 'Denmark' WHERE country_name = '덴마크';
UPDATE countries SET country_name_en = 'Finland' WHERE country_name = '핀란드';
UPDATE countries SET country_name_en = 'Poland' WHERE country_name = '폴란드';
UPDATE countries SET country_name_en = 'Austria' WHERE country_name = '오스트리아';
UPDATE countries SET country_name_en = 'Belgium' WHERE country_name = '벨기에';
UPDATE countries SET country_name_en = 'Portugal' WHERE country_name = '포르투갈';
UPDATE countries SET country_name_en = 'Greece' WHERE country_name = '그리스';
UPDATE countries SET country_name_en = 'Turkey' WHERE country_name = '터키';
UPDATE countries SET country_name_en = 'Saudi Arabia' WHERE country_name = '사우디아라비아';
UPDATE countries SET country_name_en = 'United Arab Emirates' WHERE country_name = '아랍에미리트';
UPDATE countries SET country_name_en = 'Israel' WHERE country_name = '이스라엘';
UPDATE countries SET country_name_en = 'Egypt' WHERE country_name = '이집트';
UPDATE countries SET country_name_en = 'South Africa' WHERE country_name = '남아프리카공화국';
UPDATE countries SET country_name_en = 'Argentina' WHERE country_name = '아르헨티나';
UPDATE countries SET country_name_en = 'Chile' WHERE country_name = '칠레';
UPDATE countries SET country_name_en = 'New Zealand' WHERE country_name = '뉴질랜드';
UPDATE countries SET country_name_en = 'Czech Republic' WHERE country_name = '체코';
UPDATE countries SET country_name_en = 'Hungary' WHERE country_name = '헝가리';
UPDATE countries SET country_name_en = 'Romania' WHERE country_name = '루마니아';
UPDATE countries SET country_name_en = 'Ireland' WHERE country_name = '아일랜드';
UPDATE countries SET country_name_en = 'Ukraine' WHERE country_name = '우크라이나';
UPDATE countries SET country_name_en = 'Pakistan' WHERE country_name = '파키스탄';
UPDATE countries SET country_name_en = 'Bangladesh' WHERE country_name = '방글라데시';
*/

-- 4. 변경사항 확인 쿼리
/*
SELECT 
    id,
    country_name,
    country_name_en,
    rank
FROM countries
ORDER BY rank;
*/

-- 5. 롤백 스크립트 (필요시)
/*
ALTER TABLE countries 
DROP COLUMN IF EXISTS country_name_en;
*/