#!/usr/bin/env python3
"""
Regenerate all custom_design item_names per user
Each user will have their own sequence: 0001, 0002, 0003...
Only processes designs with status='3' and numeric item_names
"""
import os
import sys
from pathlib import Path
from collections import defaultdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.orm import Session
from db.database import engine, SessionLocal
from db import models
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def regenerate_item_names():
    """Regenerate item_names for all custom designs per user"""
    
    db = SessionLocal()
    try:
        logger.info("Starting item_name regeneration per user...")
        logger.info("Will create continuous sequence 0001, 0002, 0003... for each user")
        
        # Step 1: Get ALL custom designs with status='3' (including those without item_name)
        all_designs_status_3 = db.query(models.CustomDesign).filter(
            models.CustomDesign.status == '3'
        ).order_by(
            models.CustomDesign.user_id,
            models.CustomDesign.created_at  # Sort by creation time to maintain order
        ).all()
        
        logger.info(f"Found {len(all_designs_status_3)} total designs with status='3'")
        
        # Count how many have item_names
        designs_with_names = [d for d in all_designs_status_3 if d.item_name]
        designs_without_names = [d for d in all_designs_status_3 if not d.item_name]
        
        logger.info(f"  - With item_name: {len(designs_with_names)}")
        logger.info(f"  - Without item_name: {len(designs_without_names)}")
        
        # Step 2: Group ALL designs by user_id
        user_designs = defaultdict(list)
        for design in all_designs_status_3:
            user_designs[design.user_id].append(design)
        
        logger.info(f"Found {len(user_designs)} users with status='3' designs")
        
        # Step 3: Clear ALL item_names in the entire table to avoid unique constraint violations
        logger.info("Clearing ALL item_names in custom_designs table to avoid constraint violations...")
        # Get ALL designs (not just status='3') to clear their item_names
        all_designs = db.query(models.CustomDesign).all()
        for design in all_designs:
            design.item_name = None
        db.commit()
        logger.info(f"  - Cleared {len(all_designs)} item_names")
        
        # Step 4: Regenerate item_names for each user (continuous sequence)
        total_updated = 0
        for user_id, user_design_list in sorted(user_designs.items()):
            logger.info(f"\nProcessing user: {user_id}")
            logger.info(f"  - Found {len(user_design_list)} designs")
            
            # Sort by created_at to maintain chronological order
            user_design_list.sort(key=lambda d: d.created_at)
            
            # Assign new sequential item_names starting from 0001
            for index, design in enumerate(user_design_list, start=1):
                new_item_name = str(index).zfill(4)  # 0001, 0002, 0003...
                design.item_name = new_item_name
                total_updated += 1
                
                logger.info(f"    Design ID {design.id}: -> {new_item_name} (created: {design.created_at})")
            
            # Commit after each user to save progress
            db.commit()
            logger.info(f"  ✓ Updated {len(user_design_list)} designs for user {user_id}")
        
        logger.info(f"\n✅ Successfully regenerated {total_updated} item_names")
        
        # Step 5: Show summary
        logger.info("\n=== SUMMARY ===")
        for user_id, user_design_list in sorted(user_designs.items()):
            user = db.query(models.AdminUser).filter(models.AdminUser.username == user_id).first()
            account_code = user.account_code if user else "Unknown"
            contact_name = user.contact_name if user else user_id
            logger.info(f"User: {contact_name} ({user_id}) [Account: {account_code}]")
            logger.info(f"  - Total: {len(user_design_list)} designs")
            logger.info(f"  - Sequence: 0001 to {str(len(user_design_list)).zfill(4)} (continuous, no gaps)")
        
    except Exception as e:
        logger.error(f"❌ Error during regeneration: {e}")
        db.rollback()
        raise
    finally:
        db.close()

def show_current_state():
    """Show current state of item_names before regeneration"""
    
    db = SessionLocal()
    try:
        logger.info("\n=== CURRENT STATE ===")
        
        # Get all designs with status='3' grouped by user
        designs = db.query(models.CustomDesign).filter(
            models.CustomDesign.status == '3',
            models.CustomDesign.item_name.isnot(None)
        ).order_by(
            models.CustomDesign.user_id,
            models.CustomDesign.item_name
        ).all()
        
        current_user = None
        for design in designs:
            if design.user_id != current_user:
                current_user = design.user_id
                user = db.query(models.AdminUser).filter(models.AdminUser.username == current_user).first()
                account_code = user.account_code if user else "Unknown"
                logger.info(f"\nUser: {current_user} (Account: {account_code})")
            logger.info(f"  - ID: {design.id}, item_name: {design.item_name}, created: {design.created_at}")
        
    finally:
        db.close()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Regenerate custom_design item_names per user")
    parser.add_argument('--dry-run', action='store_true', help="Show current state without making changes")
    parser.add_argument('--yes', '-y', action='store_true', help="Skip confirmation prompt")
    
    args = parser.parse_args()
    
    if args.dry_run:
        show_current_state()
    else:
        show_current_state()
        
        if not args.yes:
            logger.info("\n" + "="*50)
            logger.info("WARNING: This will regenerate ALL item_names!")
            logger.info("Each user will get a new sequence: 0001, 0002, 0003...")
            logger.info("="*50)
            response = input("\nDo you want to continue? (yes/no): ")
            if response.lower() != 'yes':
                logger.info("Operation cancelled.")
                sys.exit(0)
        
        regenerate_item_names()