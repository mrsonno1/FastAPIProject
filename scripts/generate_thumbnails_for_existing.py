"""
Script to generate thumbnails for existing images in the database
Run this after applying the database migration to populate thumbnail_url for existing records
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

def generate_thumbnails_for_existing_images():
    """Generate thumbnails for all existing images that don't have thumbnails"""
    db: Session = SessionLocal()
    
    try:
        # Process Images table
        print("Processing Images table...")
        images = db.query(models.Image).filter(
            models.Image.thumbnail_url == None,
            models.Image.public_url != None
        ).all()
        
        for i, image in enumerate(images):
            print(f"Processing image {i+1}/{len(images)}: {image.display_name}")
            try:
                thumbnail_url = thumbnail_service.create_thumbnail_from_url(image.public_url)
                if thumbnail_url:
                    image.thumbnail_url = thumbnail_url
                    db.commit()
                    print(f"  ✓ Thumbnail created for {image.display_name}")
                else:
                    print(f"  ✗ Failed to create thumbnail for {image.display_name}")
            except Exception as e:
                print(f"  ✗ Error processing {image.display_name}: {str(e)}")
            time.sleep(0.1)  # Small delay to avoid overwhelming the server
        
        # Process Brands table
        print("\nProcessing Brands table...")
        brands = db.query(models.Brand).filter(
            models.Brand.thumbnail_url == None,
            models.Brand.brand_image_url != None
        ).all()
        
        for i, brand in enumerate(brands):
            print(f"Processing brand {i+1}/{len(brands)}: {brand.brand_name}")
            try:
                thumbnail_url = thumbnail_service.create_thumbnail_from_url(brand.brand_image_url)
                if thumbnail_url:
                    brand.thumbnail_url = thumbnail_url
                    db.commit()
                    print(f"  ✓ Thumbnail created for {brand.brand_name}")
                else:
                    print(f"  ✗ Failed to create thumbnail for {brand.brand_name}")
            except Exception as e:
                print(f"  ✗ Error processing {brand.brand_name}: {str(e)}")
            time.sleep(0.1)
        
        # Process CustomDesign table
        print("\nProcessing CustomDesign table...")
        custom_designs = db.query(models.CustomDesign).filter(
            models.CustomDesign.thumbnail_url == None,
            models.CustomDesign.main_image_url != None
        ).all()
        
        for i, design in enumerate(custom_designs):
            print(f"Processing design {i+1}/{len(custom_designs)}: {design.item_name}")
            try:
                thumbnail_url = thumbnail_service.create_thumbnail_from_url(design.main_image_url)
                if thumbnail_url:
                    design.thumbnail_url = thumbnail_url
                    db.commit()
                    print(f"  ✓ Thumbnail created for {design.item_name}")
                else:
                    print(f"  ✗ Failed to create thumbnail for {design.item_name}")
            except Exception as e:
                print(f"  ✗ Error processing {design.item_name}: {str(e)}")
            time.sleep(0.1)
        
        # Process Portfolio table
        print("\nProcessing Portfolio table...")
        portfolios = db.query(models.Portfolio).filter(
            models.Portfolio.thumbnail_url == None,
            models.Portfolio.main_image_url != None,
            models.Portfolio.is_deleted == False
        ).all()
        
        for i, portfolio in enumerate(portfolios):
            print(f"Processing portfolio {i+1}/{len(portfolios)}: {portfolio.design_name}")
            try:
                thumbnail_url = thumbnail_service.create_thumbnail_from_url(portfolio.main_image_url)
                if thumbnail_url:
                    portfolio.thumbnail_url = thumbnail_url
                    db.commit()
                    print(f"  ✓ Thumbnail created for {portfolio.design_name}")
                else:
                    print(f"  ✗ Failed to create thumbnail for {portfolio.design_name}")
            except Exception as e:
                print(f"  ✗ Error processing {portfolio.design_name}: {str(e)}")
            time.sleep(0.1)
        
        print("\nThumbnail generation completed!")
        print(f"Processed: {len(images)} images, {len(brands)} brands, {len(custom_designs)} designs, {len(portfolios)} portfolios")
        
    except Exception as e:
        print(f"Fatal error: {str(e)}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    generate_thumbnails_for_existing_images()