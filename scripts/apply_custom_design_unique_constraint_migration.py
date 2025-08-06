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
    
    migration_sql = """
    -- Step 1: Drop the existing unique constraint on item_name
    ALTER TABLE custom_designs DROP CONSTRAINT IF EXISTS custom_designs_item_name_key;
    
    -- Step 2: Create a new composite unique constraint on (user_id, item_name)
    -- This allows the same item_name for different users, but prevents duplicates for the same user
    ALTER TABLE custom_designs ADD CONSTRAINT IF NOT EXISTS custom_designs_user_item_unique UNIQUE (user_id, item_name);
    """
    
    try:
        with engine.begin() as conn:
            # Execute migration
            for statement in migration_sql.split(';'):
                statement = statement.strip()
                if statement:
                    logger.info(f"Executing: {statement[:100]}...")
                    conn.execute(text(statement))
            
        logger.info("✅ Migration completed successfully!")
        logger.info("Now different users can have the same item_name (e.g., User A: 0001, User B: 0001)")
        
    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        raise

if __name__ == "__main__":
    logger.info("Starting custom_designs unique constraint migration...")
    apply_migration()