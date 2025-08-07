#!/usr/bin/env python3
"""
언어 설정 마이그레이션 스크립트
account 테이블에 language_preference 컬럼을 추가합니다.
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import text
from db.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_migration():
    """언어 설정 컬럼 추가 마이그레이션 적용"""
    
    migration_sql = """
    -- account 테이블에 language_preference 컬럼 추가
    ALTER TABLE account 
    ADD COLUMN IF NOT EXISTS language_preference VARCHAR(10) NOT NULL DEFAULT 'ko';
    """
    
    try:
        with engine.connect() as conn:
            # 트랜잭션 시작
            with conn.begin():
                # 컬럼이 이미 존재하는지 확인
                check_column = text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name = 'account' 
                    AND column_name = 'language_preference'
                """)
                
                result = conn.execute(check_column).fetchone()
                
                if result:
                    logger.info("language_preference 컬럼이 이미 존재합니다.")
                else:
                    # 마이그레이션 실행
                    conn.execute(text(migration_sql))
                    logger.info("language_preference 컬럼이 성공적으로 추가되었습니다.")
                    
                    # 기존 사용자들의 기본값 설정
                    update_sql = text("""
                        UPDATE account 
                        SET language_preference = 'ko' 
                        WHERE language_preference IS NULL
                    """)
                    conn.execute(update_sql)
                    logger.info("기존 사용자들의 언어 설정을 한국어(ko)로 초기화했습니다.")
                    
    except Exception as e:
        logger.error(f"마이그레이션 실행 중 오류 발생: {e}")
        raise

def rollback_migration():
    """마이그레이션 롤백 (필요시 사용)"""
    
    rollback_sql = """
    -- language_preference 컬럼 제거
    ALTER TABLE account 
    DROP COLUMN IF EXISTS language_preference;
    """
    
    try:
        with engine.connect() as conn:
            with conn.begin():
                conn.execute(text(rollback_sql))
                logger.info("language_preference 컬럼이 제거되었습니다.")
    except Exception as e:
        logger.error(f"롤백 중 오류 발생: {e}")
        raise

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="언어 설정 마이그레이션 스크립트")
    parser.add_argument('--rollback', action='store_true', 
                       help='마이그레이션을 롤백합니다')
    
    args = parser.parse_args()
    
    if args.rollback:
        rollback_migration()
    else:
        apply_migration()
        print("\n마이그레이션이 완료되었습니다.")
        print("서버를 재시작하면 언어 설정 기능이 정상 작동합니다.")
        print("\n사용 방법:")
        print("1. /unity/locale_kr - 한국어로 설정")
        print("2. /unity/locale_en - 영어로 설정")
        print("3. /unity/current_locale - 현재 언어 확인")
        print("\n설정된 언어는 데이터베이스에 영구 저장됩니다.")