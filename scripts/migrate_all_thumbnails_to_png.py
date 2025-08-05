"""
모든 기존 이미지의 썸네일을 PNG 형식으로 재생성하는 마이그레이션 스크립트
기존 썸네일 URL과 상관없이 메인 이미지에서 새로운 PNG 썸네일을 생성합니다.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Load environment variables from .env file
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.orm import Session
from db.database import SessionLocal
from db import models
from services.thumbnail_service import thumbnail_service
import time
import argparse
from datetime import datetime

class ThumbnailMigration:
    def __init__(self, test_mode=False, batch_size=10):
        self.test_mode = test_mode
        self.batch_size = batch_size
        self.stats = {
            'total': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0
        }
        self.failed_records = []
        
    def log(self, message):
        """로그 메시지 출력"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {message}")
        
    def process_table(self, db: Session, model_class, table_name, image_url_field, display_field):
        """특정 테이블의 썸네일을 처리"""
        self.log(f"Processing {table_name} table...")
        
        # 쿼리 빌드
        query = db.query(model_class)
        
        # main_image_url이 있는 레코드만 조회
        if hasattr(model_class, image_url_field):
            query = query.filter(getattr(model_class, image_url_field) != None)
        
        # is_deleted가 있는 경우 삭제되지 않은 레코드만
        if hasattr(model_class, 'is_deleted'):
            query = query.filter(model_class.is_deleted == False)
            
        # 테스트 모드인 경우 제한
        if self.test_mode:
            query = query.limit(5)
            
        records = query.all()
        total_records = len(records)
        
        self.log(f"Found {total_records} records to process in {table_name}")
        
        for i, record in enumerate(records):
            record_id = getattr(record, 'id')
            display_name = getattr(record, display_field, f"ID: {record_id}")
            image_url = getattr(record, image_url_field)
            
            self.log(f"[{i+1}/{total_records}] Processing {display_name}")
            self.stats['total'] += 1
            
            try:
                # PNG 썸네일 생성
                thumbnail_url = thumbnail_service.create_thumbnail_from_url(image_url)
                
                if thumbnail_url:
                    # 썸네일 URL 업데이트
                    record.thumbnail_url = thumbnail_url
                    db.commit()
                    self.stats['success'] += 1
                    self.log(f"  ✓ PNG thumbnail created: {thumbnail_url}")
                else:
                    self.stats['failed'] += 1
                    self.failed_records.append({
                        'table': table_name,
                        'id': record_id,
                        'name': display_name,
                        'reason': 'Failed to create thumbnail'
                    })
                    self.log(f"  ✗ Failed to create thumbnail")
                    
            except Exception as e:
                db.rollback()
                self.stats['failed'] += 1
                self.failed_records.append({
                    'table': table_name,
                    'id': record_id,
                    'name': display_name,
                    'reason': str(e)
                })
                self.log(f"  ✗ Error: {str(e)}")
                
            # 서버 부하 방지를 위한 지연
            time.sleep(0.1)
            
            # 배치 단위로 진행 상황 표시
            if (i + 1) % self.batch_size == 0:
                self.log(f"Progress: {i+1}/{total_records} completed")
                
    def run(self):
        """마이그레이션 실행"""
        db: Session = SessionLocal()
        
        try:
            start_time = time.time()
            self.log("Starting thumbnail migration to PNG format...")
            
            if self.test_mode:
                self.log("*** RUNNING IN TEST MODE - Processing only 5 records per table ***")
            
            # 각 테이블 처리
            tables = [
                (models.Brand, 'brands', 'brand_image_url', 'brand_name'),
                (models.Image, 'images', 'public_url', 'display_name'),
                (models.CustomDesign, 'custom_designs', 'main_image_url', 'item_name'),
                (models.Portfolio, 'portfolios', 'main_image_url', 'design_name'),
                (models.Releasedproduct, 'releasedproducts', 'main_image_url', 'design_name')
            ]
            
            for model_class, table_name, image_field, display_field in tables:
                self.process_table(db, model_class, table_name, image_field, display_field)
                self.log(f"Completed {table_name}\n")
                
            # 최종 통계
            elapsed_time = time.time() - start_time
            self.log("="*50)
            self.log("Migration completed!")
            self.log(f"Total time: {elapsed_time:.2f} seconds")
            self.log(f"Total processed: {self.stats['total']}")
            self.log(f"Success: {self.stats['success']}")
            self.log(f"Failed: {self.stats['failed']}")
            self.log(f"Skipped: {self.stats['skipped']}")
            
            # 실패한 레코드 표시
            if self.failed_records:
                self.log("\nFailed records:")
                for record in self.failed_records:
                    self.log(f"  - {record['table']} ID:{record['id']} ({record['name']}): {record['reason']}")
                    
            # 성공률 계산
            if self.stats['total'] > 0:
                success_rate = (self.stats['success'] / self.stats['total']) * 100
                self.log(f"\nSuccess rate: {success_rate:.2f}%")
                
        except Exception as e:
            self.log(f"Fatal error: {str(e)}")
            db.rollback()
            import traceback
            traceback.print_exc()
        finally:
            db.close()

def main():
    parser = argparse.ArgumentParser(description='Migrate all thumbnails to PNG format')
    parser.add_argument('--test', action='store_true', help='Run in test mode (process only 5 records per table)')
    parser.add_argument('--batch-size', type=int, default=10, help='Batch size for progress reporting (default: 10)')
    
    args = parser.parse_args()
    
    # 경고 메시지
    if not args.test:
        print("\n" + "="*60)
        print("WARNING: This will regenerate ALL thumbnails as PNG format!")
        print("This process may take a long time depending on the number of records.")
        print("It's recommended to backup your database before proceeding.")
        print("="*60 + "\n")
        
        response = input("Do you want to continue? (yes/no): ")
        if response.lower() != 'yes':
            print("Migration cancelled.")
            return
            
    # 마이그레이션 실행
    migration = ThumbnailMigration(test_mode=args.test, batch_size=args.batch_size)
    migration.run()

if __name__ == "__main__":
    main()