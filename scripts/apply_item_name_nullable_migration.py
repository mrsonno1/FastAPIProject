"""
Apply migration to make item_name nullable in custom_designs table
"""
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from db.database import engine


def apply_migration():
    """Apply the migration to make item_name nullable"""
    
    migration_file = Path(__file__).parent.parent / "migrations" / "make_item_name_nullable.sql"
    
    try:
        # Read migration SQL
        with open(migration_file, 'r', encoding='utf-8') as f:
            migration_sql = f.read()
        
        # Execute migration
        with engine.connect() as conn:
            # Split by semicolon and execute each statement
            statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
            
            for statement in statements:
                if statement and not statement.startswith('--'):
                    print(f"Executing: {statement[:50]}...")
                    conn.execute(text(statement))
                    conn.commit()
            
            print("\nMigration applied successfully!")
            
            # Verify the change - check if constraint was dropped
            result = conn.execute(text("""
                SELECT 
                    c.column_name,
                    c.is_nullable,
                    c.column_default,
                    tc.constraint_type
                FROM information_schema.columns c
                LEFT JOIN information_schema.key_column_usage kcu 
                    ON c.table_name = kcu.table_name 
                    AND c.column_name = kcu.column_name
                LEFT JOIN information_schema.table_constraints tc 
                    ON kcu.constraint_name = tc.constraint_name
                WHERE c.table_name = 'custom_designs' 
                AND c.column_name = 'item_name'
            """))
            
            row = result.fetchone()
            if row:
                print(f"\nVerification - item_name is_nullable: {row[1]}")
            
    except Exception as e:
        print(f"Error applying migration: {e}")
        return False
    
    return True


if __name__ == "__main__":
    print("Applying migration to make item_name nullable...")
    if apply_migration():
        print("\nMigration completed successfully!")
        print("\nNext steps:")
        print("1. Test creating a custom design without item_name")
        print("2. Test updating status to 3 to generate item_name")
    else:
        print("\nMigration failed!")
        print("Check the error message above and try again.")