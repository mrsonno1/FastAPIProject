"""
released_product 테이블의 thumbnail_url을 채우는 스크립트
기존 main_image_url을 기반으로 썸네일을 생성합니다.
"""
import os
import sys
from pathlib import Path
import requests
from io import BytesIO

# 프로젝트 루트 디렉토리를 Python 경로에 추가
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# .env 파일 로드
from dotenv import load_dotenv
load_dotenv()

from sqlalchemy.orm import Session
from db.database import SessionLocal, engine
from db import models
from services.thumbnail_service import thumbnail_service
from services.storage_service import storage_service

def download_image(url):
    """URL에서 이미지를 다운로드하여 바이트로 반환"""
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        return response.content
    except Exception as e:
        print(f"Failed to download image from {url}: {e}")
        return None

def fill_thumbnails():
    """released_product 테이블의 모든 레코드에 대해 썸네일 생성"""
    
    db: Session = SessionLocal()
    
    try:
        # thumbnail_url이 없는 모든 released_product 조회
        products = db.query(models.Releasedproduct).filter(
            models.Releasedproduct.thumbnail_url == None
        ).all()
        
        print(f"Found {len(products)} products without thumbnails")
        
        success_count = 0
        failed_count = 0
        
        for i, product in enumerate(products, 1):
            print(f"\nProcessing {i}/{len(products)}: {product.design_name}")
            
            if not product.main_image_url:
                print(f"  - Skipping: No main_image_url")
                failed_count += 1
                continue
            
            try:
                # 이미지 다운로드
                print(f"  - Downloading image from: {product.main_image_url}")
                image_data = download_image(product.main_image_url)
                
                if not image_data:
                    print(f"  - Failed to download image")
                    failed_count += 1
                    continue
                
                # 썸네일 생성 및 업로드
                print(f"  - Creating thumbnail...")
                thumbnail_url = thumbnail_service.create_and_upload_thumbnail(
                    image_data, 
                    f"released_product_{product.id}.jpg"
                )
                
                if thumbnail_url:
                    # DB 업데이트
                    product.thumbnail_url = thumbnail_url
                    db.commit()
                    print(f"  - Success! Thumbnail URL: {thumbnail_url}")
                    success_count += 1
                else:
                    print(f"  - Failed to create thumbnail")
                    failed_count += 1
                    
            except Exception as e:
                print(f"  - Error: {e}")
                failed_count += 1
                db.rollback()
        
        print(f"\n=== Summary ===")
        print(f"Total processed: {len(products)}")
        print(f"Success: {success_count}")
        print(f"Failed: {failed_count}")
        
    except Exception as e:
        print(f"Fatal error: {e}")
        db.rollback()
    finally:
        db.close()

def fill_thumbnails_simple():
    """
    간단한 방법: main_image_url을 그대로 thumbnail_url로 복사
    (실제 썸네일 생성 없이 임시로 사용)
    """
    
    db: Session = SessionLocal()
    
    try:
        # thumbnail_url이 없는 모든 released_product 조회
        result = db.query(models.Releasedproduct).filter(
            models.Releasedproduct.thumbnail_url == None,
            models.Releasedproduct.main_image_url != None
        ).update({
            models.Releasedproduct.thumbnail_url: models.Releasedproduct.main_image_url
        })
        
        db.commit()
        
        print(f"Updated {result} products with thumbnail URLs (copied from main_image_url)")
        
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Fill thumbnail URLs for released products')
    parser.add_argument('--simple', action='store_true', 
                      help='Use simple mode (copy main_image_url to thumbnail_url)')
    
    args = parser.parse_args()
    
    if args.simple:
        print("Using simple mode: copying main_image_url to thumbnail_url")
        fill_thumbnails_simple()
    else:
        print("Using full mode: generating actual thumbnails")
        fill_thumbnails()