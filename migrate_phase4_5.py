"""
Phase 4.5 Migration Script

Přidává:
1. Sloupec 'custom_label' do 'dropdown_config' - pro přejmenování polí
2. Novou tabulku 'field_categories' - pro custom kategorie
3. Seed defaultních kategorií pro všechny entity
"""

import sqlite3
from datetime import datetime

def migrate_phase4_5(db_path='revize.db'):
    """Main migration function for Phase 4.5"""
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    print("=== PHASE 4.5 MIGRATION START ===")
    
    # ========================================
    # 1. Add 'custom_label' column to dropdown_config
    # ========================================
    print("\n1. Adding 'custom_label' column to dropdown_config...")
    try:
        cursor.execute("""
            ALTER TABLE dropdown_config 
            ADD COLUMN custom_label VARCHAR(255) NULL
        """)
        print("   ✓ Column 'custom_label' added successfully")
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e).lower():
            print("   ℹ Column 'custom_label' already exists, skipping...")
        else:
            raise
    
    # ========================================
    # 2. Create 'field_categories' table
    # ========================================
    print("\n2. Creating 'field_categories' table...")
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS field_categories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entity_type VARCHAR(100) NOT NULL,
                category_key VARCHAR(100) NOT NULL,
                category_label VARCHAR(255) NOT NULL,
                display_order INTEGER DEFAULT 0,
                icon VARCHAR(50) DEFAULT '📋',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(entity_type, category_key)
            )
        """)
        print("   ✓ Table 'field_categories' created successfully")
    except sqlite3.OperationalError as e:
        print(f"   ℹ Table might already exist: {e}")
    
    # ========================================
    # 3. Seed default categories
    # ========================================
    print("\n3. Seeding default categories for all entities...")
    
    entities = ['revision', 'switchboard', 'device', 'circuit', 'terminal_device']
    default_categories = [
        ('basic', 'Základní pole', '📋', 10),
        ('additional', 'Dodatečná pole', '➕', 20),
        ('measurements', 'Měření', '📊', 30),
        ('technical', 'Technické specifikace', '🔧', 40),
        ('administrative', 'Administrativní údaje', '📄', 50),
    ]
    
    for entity in entities:
        print(f"   Seeding categories for '{entity}'...")
        for cat_key, cat_label, icon, order in default_categories:
            try:
                cursor.execute("""
                    INSERT OR IGNORE INTO field_categories 
                    (entity_type, category_key, category_label, icon, display_order)
                    VALUES (?, ?, ?, ?, ?)
                """, (entity, cat_key, cat_label, icon, order))
            except Exception as e:
                print(f"      ⚠ Error inserting {entity}/{cat_key}: {e}")
        print(f"      ✓ Categories seeded for '{entity}'")
    
    # Commit changes
    conn.commit()
    
    # ========================================
    # 4. Verify migration
    # ========================================
    print("\n4. Verifying migration...")
    
    # Check custom_label column
    cursor.execute("PRAGMA table_info(dropdown_config)")
    columns = [col[1] for col in cursor.fetchall()]
    if 'custom_label' in columns:
        print("   ✓ 'custom_label' column exists in dropdown_config")
    else:
        print("   ✗ 'custom_label' column NOT found!")
    
    # Check field_categories table
    cursor.execute("""
        SELECT COUNT(*) FROM sqlite_master 
        WHERE type='table' AND name='field_categories'
    """)
    if cursor.fetchone()[0] > 0:
        print("   ✓ 'field_categories' table exists")
        
        # Count categories
        cursor.execute("SELECT COUNT(*) FROM field_categories")
        count = cursor.fetchone()[0]
        print(f"   ✓ {count} categories seeded")
    else:
        print("   ✗ 'field_categories' table NOT found!")
    
    conn.close()
    
    print("\n=== PHASE 4.5 MIGRATION COMPLETE ===")
    print("\nNext steps:")
    print("1. Restart the application")
    print("2. Test Settings UI - Field Configuration")
    print("3. Verify Drag & Drop works")
    print("4. Verify category switching works")
    print("5. Test custom category creation")

if __name__ == "__main__":
    import sys
    db_path = sys.argv[1] if len(sys.argv) > 1 else 'revize.db'
    
    print(f"Running Phase 4.5 migration on database: {db_path}")
    print(f"Timestamp: {datetime.now()}\n")
    
    # Backup reminder
    print("⚠️  IMPORTANT: Make sure you have backed up your database!")
    print("    cp revize.db revize.db.backup\n")
    
    response = input("Continue with migration? (yes/no): ")
    if response.lower() in ['yes', 'y']:
        migrate_phase4_5(db_path)
    else:
        print("Migration cancelled.")
