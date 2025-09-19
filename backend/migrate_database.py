from sqlalchemy import create_engine, text
from core.config import settings

def migrate_database():
    """Add new columns to existing tables"""
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Start a transaction
        trans = conn.begin()
        try:
            # Add main_image column to stories table
            conn.execute(text("""
                ALTER TABLE stories 
                ADD COLUMN IF NOT EXISTS main_image TEXT
            """))
            
            # Add image column to story_nodes table
            conn.execute(text("""
                ALTER TABLE story_nodes 
                ADD COLUMN IF NOT EXISTS image TEXT
            """))
            
            # Commit the transaction
            trans.commit()
            print("✅ Database migration completed successfully!")
            print("Added main_image column to stories table")
            print("Added image column to story_nodes table")
            
        except Exception as e:
            # Rollback on error
            trans.rollback()
            print(f"❌ Migration failed: {e}")
            raise

if __name__ == "__main__":
    migrate_database() 