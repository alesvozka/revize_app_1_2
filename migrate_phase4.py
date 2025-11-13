"""
PHASE 4 MIGRATION: Add field configuration columns to dropdown_config table
"""
from sqlalchemy import create_engine, text
from database import SQLALCHEMY_DATABASE_URL

def migrate_phase4():
    """Add new columns for field configuration"""
    engine = create_engine(SQLALCHEMY_DATABASE_URL)
    
    migrations = [
        # Add new columns
        "ALTER TABLE dropdown_config ADD COLUMN IF NOT EXISTS field_label VARCHAR(255)",
        "ALTER TABLE dropdown_config ADD COLUMN IF NOT EXISTS field_category VARCHAR(100)",
        "ALTER TABLE dropdown_config ADD COLUMN IF NOT EXISTS display_order INTEGER DEFAULT 0",
        "ALTER TABLE dropdown_config ADD COLUMN IF NOT EXISTS enabled BOOLEAN DEFAULT TRUE",
        "ALTER TABLE dropdown_config ADD COLUMN IF NOT EXISTS is_required BOOLEAN DEFAULT FALSE",
        "ALTER TABLE dropdown_config ADD COLUMN IF NOT EXISTS field_type VARCHAR(50) DEFAULT 'text'",
    ]
    
    with engine.connect() as conn:
        for migration in migrations:
            try:
                print(f"Executing: {migration}")
                conn.execute(text(migration))
                conn.commit()
                print("✓ Success")
            except Exception as e:
                print(f"✗ Error: {e}")
                conn.rollback()
    
    print("\n✓ Phase 4 migration completed!")

if __name__ == "__main__":
    migrate_phase4()
