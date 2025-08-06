#!/usr/bin/env python3
"""
Apply the custom_designs unique constraint migration
Changes from unique(item_name) to unique(user_id, item_name)
"""
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from db.database import engine
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def apply_migration():
    """Apply the unique constraint migration for custom_designs table"""
    
    try:
        with engine.begin() as conn:
            # Step 1: Check if the old constraint exists and drop it
            logger.info("Step 1: Dropping existing unique constraint on item_name...")
            try:
                conn.execute(text("ALTER TABLE custom_designs DROP CONSTRAINT custom_designs_item_name_key"))
                logger.info("  - Dropped custom_designs_item_name_key")
            except Exception as e:
                logger.info(f"  - Constraint custom_designs_item_name_key doesn't exist or already dropped: {e}")
            
            # Step 2: Check if the new constraint already exists
            logger.info("Step 2: Checking if new constraint already exists...")
            result = conn.execute(text("""
                SELECT COUNT(*) 
                FROM pg_constraint 
                WHERE conname = 'custom_designs_user_item_unique'
            """))
            constraint_exists = result.scalar() > 0
            
            if constraint_exists:
                logger.info("  - Constraint custom_designs_user_item_unique already exists, skipping creation")
            else:
                # Step 3: Create the new composite unique constraint
                logger.info("Step 3: Creating new composite unique constraint on (user_id, item_name)...")
                conn.execute(text(
                    "ALTER TABLE custom_designs ADD CONSTRAINT custom_designs_user_item_unique UNIQUE (user_id, item_name)"
                ))
                logger.info("  - Created custom_designs_user_item_unique")
            
        logger.info("✅ Migration completed successfully!")
        logger.info("Now different users can have the same item_name (e.g., User A: 0001, User B: 0001)")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    logger.info("Starting custom_designs unique constraint migration...")
    apply_migration()