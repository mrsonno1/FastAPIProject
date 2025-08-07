#!/usr/bin/env python3
"""
Email 중복 허용을 위한 마이그레이션 스크립트
- account 테이블의 email 컬럼에서 unique constraint를 제거합니다.
- 여러 관리자가 같은 이메일을 사용할 수 있도록 합니다.
"""

import os
import sys
from pathlib import Path

# 프로젝트 루트 디렉토리를 sys.path에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from sqlalchemy import create_engine, text
from core.config import settings
import logging

# 로깅 설정
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_migration():
    """이메일 중복 허용 마이그레이션 적용"""
    
    # 데이터베이스 연결
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.begin() as conn:
            # 1. 기존 unique constraint 제거
            logger.info("Removing unique constraint from email column...")
            conn.execute(text("ALTER TABLE account DROP CONSTRAINT IF EXISTS account_email_key"))
            
            # 2. 기존 unique index 제거
            logger.info("Dropping unique index...")
            conn.execute(text("DROP INDEX IF EXISTS ix_account_email"))
            
            # 3. 일반 index 생성 (성능을 위해)
            logger.info("Creating regular index for email column...")
            conn.execute(text("CREATE INDEX IF NOT EXISTS ix_account_email ON account(email)"))
            
            # 4. 변경사항 확인
            result = conn.execute(text("""
                SELECT constraint_name, constraint_type 
                FROM information_schema.table_constraints 
                WHERE table_name = 'account' AND constraint_type = 'UNIQUE'
            """))
            
            constraints = result.fetchall()
            logger.info(f"Remaining unique constraints on account table: {constraints}")
            
            # 5. 이메일 중복 테스트 쿼리 (실제 데이터는 변경하지 않음)
            test_result = conn.execute(text("""
                SELECT email, COUNT(*) as count 
                FROM account 
                WHERE email IS NOT NULL AND is_deleted = false
                GROUP BY email 
                HAVING COUNT(*) > 1
            """))
            
            duplicates = test_result.fetchall()
            if duplicates:
                logger.warning(f"Found existing duplicate emails: {duplicates}")
            else:
                logger.info("No duplicate emails found in existing data")
            
            logger.info("Migration completed successfully!")
            logger.info("Email duplicates are now allowed in the account table.")
            
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise
    finally:
        engine.dispose()

def rollback_migration():
    """마이그레이션 롤백 (필요시 unique constraint 다시 추가)"""
    
    engine = create_engine(settings.DATABASE_URL)
    
    try:
        with engine.begin() as conn:
            # unique constraint 다시 추가
            logger.info("Re-adding unique constraint to email column...")
            conn.execute(text("""
                ALTER TABLE account 
                ADD CONSTRAINT account_email_key UNIQUE (email)
            """))
            
            logger.info("Rollback completed successfully!")
            
    except Exception as e:
        logger.error(f"Rollback failed: {e}")
        logger.error("Note: Rollback may fail if duplicate emails already exist in the database")
        raise
    finally:
        engine.dispose()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Apply or rollback email duplicate migration")
    parser.add_argument(
        "--rollback", 
        action="store_true", 
        help="Rollback the migration (re-add unique constraint)"
    )
    
    args = parser.parse_args()
    
    if args.rollback:
        logger.info("Starting rollback...")
        rollback_migration()
    else:
        logger.info("Starting migration...")
        apply_migration()