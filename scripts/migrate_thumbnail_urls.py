"""
데이터베이스에 thumbnail_url 컬럼을 추가하는 마이그레이션 스크립트
"""
from sqlalchemy import text
from db.database import engine

def add_thumbnail_urls():
    """각 테이블에 thumbnail_url 컬럼 추가"""
    
    with engine.connect() as conn:
        # Start transaction
        trans = conn.begin()
        
        try:
            # Add thumbnail_url to releasedproducts
            conn.execute(text("""
                ALTER TABLE releasedproducts 
                ADD COLUMN IF NOT EXISTS thumbnail_url VARCHAR
            """))
            print("Added thumbnail_url to releasedproducts table")
            
            # Optionally add to other tables
            # conn.execute(text("""
            #     ALTER TABLE portfolios 
            #     ADD COLUMN IF NOT EXISTS thumbnail_url VARCHAR
            # """))
            # print("Added thumbnail_url to portfolios table")
            
            # conn.execute(text("""
            #     ALTER TABLE brands 
            #     ADD COLUMN IF NOT EXISTS thumbnail_url VARCHAR
            # """))
            # print("Added thumbnail_url to brands table")
            
            # conn.execute(text("""
            #     ALTER TABLE images 
            #     ADD COLUMN IF NOT EXISTS thumbnail_url VARCHAR
            # """))
            # print("Added thumbnail_url to images table")
            
            # conn.execute(text("""
            #     ALTER TABLE custom_designs 
            #     ADD COLUMN IF NOT EXISTS thumbnail_url VARCHAR
            # """))
            # print("Added thumbnail_url to custom_designs table")
            
            # Commit transaction
            trans.commit()
            print("Migration completed successfully!")
            
        except Exception as e:
            # Rollback on error
            trans.rollback()
            print(f"Migration failed: {e}")
            raise

if __name__ == "__main__":
    add_thumbnail_urls()