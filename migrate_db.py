#!/usr/bin/env python3
"""
🔧 REVIZE APP - Database Migration Script
==========================================
Automaticky vytvoří a aktualizuje databázovou strukturu pro PostgreSQL.

Použití při deployment:
    python migrate_db.py

Co dělá:
    1. Vytvoří všechny tabulky (pokud neexistují)
    2. Přidá chybějící sloupce do dropdown_config (Phase 4.5)
    3. Vytvoří field_categories tabulku
    4. Seed základních kategorií

Bezpečnost:
    - Idempotentní (můžeš spustit vícekrát)
    - Používá IF NOT EXISTS
    - Kontroluje každý krok
"""

import os
import sys
from sqlalchemy import create_engine, text, inspect
from sqlalchemy.exc import SQLAlchemyError

# Barvy pro výstup
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.RESET}\n")

def print_success(text):
    print(f"{Colors.GREEN}✓ {text}{Colors.RESET}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")

def print_info(text):
    print(f"  {text}")

def get_database_url():
    """Získá DATABASE_URL z environment variables"""
    database_url = os.getenv("DATABASE_URL")
    
    if not database_url:
        print_error("DATABASE_URL environment variable není nastavena!")
        print_info("Nastav ji pomocí: export DATABASE_URL='postgresql://user:pass@host:port/db'")
        sys.exit(1)
    
    # Railway používá postgres://, ale SQLAlchemy potřebuje postgresql://
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    
    return database_url

def check_column_exists(inspector, table_name, column_name):
    """Zkontroluje, zda sloupec existuje v tabulce"""
    try:
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns
    except Exception:
        return False

def check_table_exists(inspector, table_name):
    """Zkontroluje, zda tabulka existuje"""
    return table_name in inspector.get_table_names()

def create_all_tables(engine, inspector):
    """Vytvoří všechny tabulky (pokud neexistují)"""
    print_header("📋 VYTVÁŘENÍ TABULEK")
    
    tables_sql = {
        'users': """
            CREATE TABLE IF NOT EXISTS users (
                user_id SERIAL PRIMARY KEY,
                username VARCHAR(100) UNIQUE NOT NULL,
                email VARCHAR(255) UNIQUE NOT NULL,
                password_hash VARCHAR(255) NOT NULL,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            )
        """,
        'revisions': """
            CREATE TABLE IF NOT EXISTS revisions (
                revision_id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(user_id),
                revision_code VARCHAR(100),
                revision_name VARCHAR(255),
                revision_owner VARCHAR(255),
                revision_client VARCHAR(255),
                revision_address TEXT,
                revision_description TEXT,
                revision_type VARCHAR(100),
                revision_date_of_previous_revision DATE,
                revision_start_date DATE,
                revision_end_date DATE,
                revision_date_of_creation DATE,
                revision_recommended_date_for_next_revision DATE,
                revision_number_of_copies_technician INTEGER,
                revision_number_of_copies_owner INTEGER,
                revision_number_of_copies_contractor INTEGER,
                revision_number_of_copies_client INTEGER,
                revision_attachment VARCHAR(255),
                revision_attachment_submitter VARCHAR(255),
                revision_attachment_producer VARCHAR(255),
                revision_attachment_date_of_creation DATE,
                revision_technician VARCHAR(255),
                revision_certificate_number VARCHAR(100),
                revision_authorization_number VARCHAR(100),
                revision_project_documentation TEXT,
                revision_contractor VARCHAR(255),
                revision_short_description TEXT,
                revision_measuring_instrument_manufacturer_type VARCHAR(255),
                revision_measuring_instrument_serial_number VARCHAR(100),
                revision_measuring_instrument_calibration VARCHAR(255),
                revision_measuring_instrument_calibration_validity DATE,
                revision_overall_assessment TEXT
            )
        """,
        'switchboards': """
            CREATE TABLE IF NOT EXISTS switchboards (
                switchboard_id SERIAL PRIMARY KEY,
                revision_id INTEGER NOT NULL REFERENCES revisions(revision_id),
                switchboard_name VARCHAR(255),
                switchboard_description TEXT,
                switchboard_location VARCHAR(255),
                switchboard_order INTEGER DEFAULT 0,
                switchboard_type VARCHAR(100),
                switchboard_serial_number VARCHAR(100),
                switchboard_production_date DATE,
                switchboard_ip_rating VARCHAR(50),
                switchboard_impact_protection VARCHAR(50),
                switchboard_protection_class VARCHAR(50),
                switchboard_rated_current FLOAT,
                switchboard_rated_voltage FLOAT,
                switchboard_manufacturer VARCHAR(255),
                switchboard_manufacturer_address TEXT,
                switchboard_standards TEXT,
                switchboard_enclosure_type VARCHAR(100),
                switchboard_enclosure_manufacturer VARCHAR(255),
                switchboard_enclosure_installation_method VARCHAR(255),
                switchboard_superior_switchboard VARCHAR(255),
                switchboard_superior_circuit_breaker_rated_current FLOAT,
                switchboard_superior_circuit_breaker_trip_characteristic VARCHAR(50),
                switchboard_superior_circuit_breaker_manufacturer VARCHAR(255),
                switchboard_superior_circuit_breaker_model VARCHAR(100),
                switchboard_main_switch VARCHAR(255),
                switchboard_note TEXT,
                switchboard_cable VARCHAR(255),
                switchboard_cable_installation_method VARCHAR(255)
            )
        """,
        'switchboard_measurements': """
            CREATE TABLE IF NOT EXISTS switchboard_measurements (
                measurement_id SERIAL PRIMARY KEY,
                switchboard_id INTEGER UNIQUE NOT NULL REFERENCES switchboards(switchboard_id),
                measurements_switchboard_insulation_resistance FLOAT,
                measurements_switchboard_loop_impedance_min FLOAT,
                measurements_switchboard_loop_impedance_max FLOAT,
                measurements_switchboard_rcd_trip_time_ms FLOAT,
                measurements_switchboard_rcd_test_current_ma FLOAT,
                measurements_switchboard_earth_resistance FLOAT
            )
        """,
        'switchboard_devices': """
            CREATE TABLE IF NOT EXISTS switchboard_devices (
                device_id SERIAL PRIMARY KEY,
                switchboard_id INTEGER NOT NULL REFERENCES switchboards(switchboard_id),
                parent_device_id INTEGER REFERENCES switchboard_devices(device_id),
                switchboard_device_position VARCHAR(100),
                switchboard_device_type VARCHAR(100),
                switchboard_device_manufacturer VARCHAR(255),
                switchboard_device_model VARCHAR(100),
                switchboard_device_trip_characteristic VARCHAR(50),
                switchboard_device_rated_current FLOAT,
                switchboard_device_residual_current_ma FLOAT,
                switchboard_device_sub_devices TEXT,
                switchboard_device_poles INTEGER,
                switchboard_device_module_width FLOAT
            )
        """,
        'circuits': """
            CREATE TABLE IF NOT EXISTS circuits (
                circuit_id SERIAL PRIMARY KEY,
                device_id INTEGER NOT NULL REFERENCES switchboard_devices(device_id),
                circuit_number VARCHAR(100),
                circuit_room VARCHAR(255),
                circuit_description TEXT,
                circuit_description_from_switchboard TEXT,
                circuit_number_of_outlets INTEGER,
                circuit_cable_termination VARCHAR(255),
                circuit_cable VARCHAR(255),
                circuit_cable_installation_method VARCHAR(255)
            )
        """,
        'circuit_measurements': """
            CREATE TABLE IF NOT EXISTS circuit_measurements (
                measurement_id SERIAL PRIMARY KEY,
                circuit_id INTEGER UNIQUE NOT NULL REFERENCES circuits(circuit_id),
                measurements_circuit_insulation_resistance FLOAT,
                measurements_circuit_loop_impedance_min FLOAT,
                measurements_circuit_loop_impedance_max FLOAT,
                measurements_circuit_rcd_trip_time_ms FLOAT,
                measurements_circuit_rcd_test_current_ma FLOAT,
                measurements_circuit_earth_resistance FLOAT,
                measurements_circuit_continuity FLOAT,
                measurements_circuit_order_of_phases VARCHAR(50)
            )
        """,
        'terminal_devices': """
            CREATE TABLE IF NOT EXISTS terminal_devices (
                terminal_device_id SERIAL PRIMARY KEY,
                circuit_id INTEGER NOT NULL REFERENCES circuits(circuit_id),
                terminal_device_type VARCHAR(100),
                terminal_device_manufacturer VARCHAR(255),
                terminal_device_model VARCHAR(100),
                terminal_device_marking VARCHAR(100),
                terminal_device_power FLOAT,
                terminal_device_ip_rating VARCHAR(50),
                terminal_device_protection_class VARCHAR(50),
                terminal_device_serial_number VARCHAR(100),
                terminal_device_supply_type VARCHAR(100),
                terminal_device_installation_method VARCHAR(255)
            )
        """,
        'dropdown_sources': """
            CREATE TABLE IF NOT EXISTS dropdown_sources (
                id SERIAL PRIMARY KEY,
                category VARCHAR(100) NOT NULL,
                value VARCHAR(255) NOT NULL,
                display_order INTEGER DEFAULT 0,
                created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
            );
            CREATE INDEX IF NOT EXISTS idx_dropdown_sources_category ON dropdown_sources(category);
        """,
        'dropdown_config': """
            CREATE TABLE IF NOT EXISTS dropdown_config (
                id SERIAL PRIMARY KEY,
                entity_type VARCHAR(100) NOT NULL,
                field_name VARCHAR(255) NOT NULL,
                dropdown_enabled BOOLEAN DEFAULT FALSE,
                dropdown_category VARCHAR(100)
            )
        """,
    }
    
    with engine.connect() as conn:
        for table_name, sql in tables_sql.items():
            try:
                if not check_table_exists(inspector, table_name):
                    conn.execute(text(sql))
                    conn.commit()
                    print_success(f"Tabulka '{table_name}' vytvořena")
                else:
                    print_info(f"Tabulka '{table_name}' již existuje")
            except Exception as e:
                print_error(f"Chyba při vytváření tabulky '{table_name}': {e}")

def migrate_dropdown_config(engine, inspector):
    """Přidá chybějící sloupce do dropdown_config (Phase 4.5)"""
    print_header("🔧 MIGRACE DROPDOWN_CONFIG (Phase 4.5)")
    
    # Sloupce, které je potřeba přidat
    columns_to_add = {
        'field_label': 'VARCHAR(255)',
        'field_category': 'VARCHAR(100)',
        'display_order': 'INTEGER DEFAULT 0',
        'enabled': 'BOOLEAN DEFAULT TRUE',
        'is_required': 'BOOLEAN DEFAULT FALSE',
        'field_type': "VARCHAR(50) DEFAULT 'text'",
        'custom_label': 'VARCHAR(255)',
    }
    
    # Zkontroluj, které sloupce chybí
    missing_columns = []
    for col_name in columns_to_add.keys():
        if not check_column_exists(inspector, 'dropdown_config', col_name):
            missing_columns.append(col_name)
            print_warning(f"Sloupec '{col_name}' chybí")
        else:
            print_info(f"Sloupec '{col_name}' již existuje")
    
    if not missing_columns:
        print_success("Všechny sloupce již existují! Migrace není potřeba.")
        return True
    
    print(f"\n{Colors.YELLOW}Bude přidáno {len(missing_columns)} sloupců{Colors.RESET}")
    
    try:
        with engine.connect() as conn:
            trans = conn.begin()
            
            try:
                # Přidat chybějící sloupce
                for col_name in missing_columns:
                    col_definition = columns_to_add[col_name]
                    sql = f"ALTER TABLE dropdown_config ADD COLUMN IF NOT EXISTS {col_name} {col_definition};"
                    
                    print_info(f"Přidávám sloupec: {col_name}...")
                    conn.execute(text(sql))
                
                # Nastavit výchozí hodnoty pro existující záznamy
                print("\n" + Colors.BLUE + "Aktualizuji výchozí hodnoty..." + Colors.RESET)
                
                update_statements = [
                    "UPDATE dropdown_config SET display_order = 0 WHERE display_order IS NULL",
                    "UPDATE dropdown_config SET enabled = TRUE WHERE enabled IS NULL",
                    "UPDATE dropdown_config SET is_required = FALSE WHERE is_required IS NULL",
                    "UPDATE dropdown_config SET field_type = 'text' WHERE field_type IS NULL"
                ]
                
                for statement in update_statements:
                    conn.execute(text(statement))
                
                trans.commit()
                print_success("Migrace dropdown_config úspěšně dokončena!")
                return True
                
            except Exception as e:
                trans.rollback()
                print_error(f"Chyba během migrace: {e}")
                print_info("Transakce byla vrácena zpět (ROLLBACK)")
                return False
                
    except Exception as e:
        print_error(f"Chyba při připojení k databázi: {e}")
        return False

def create_field_categories_table(engine, inspector):
    """Vytvoří tabulku field_categories"""
    print_header("📋 VYTVÁŘENÍ FIELD_CATEGORIES")
    
    if check_table_exists(inspector, 'field_categories'):
        print_info("Tabulka 'field_categories' již existuje")
        return True
    
    sql = """
        CREATE TABLE IF NOT EXISTS field_categories (
            id SERIAL PRIMARY KEY,
            entity_type VARCHAR(100) NOT NULL,
            category_key VARCHAR(100) NOT NULL,
            category_label VARCHAR(255) NOT NULL,
            display_order INTEGER DEFAULT 0,
            icon VARCHAR(50) DEFAULT '📋',
            created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(entity_type, category_key)
        )
    """
    
    try:
        with engine.connect() as conn:
            conn.execute(text(sql))
            conn.commit()
            print_success("Tabulka 'field_categories' vytvořena")
            return True
    except Exception as e:
        print_error(f"Chyba při vytváření field_categories: {e}")
        return False

def seed_field_categories(engine):
    """Seed základních kategorií pro všechny entity"""
    print_header("🌱 SEED KATEGORIÍ")
    
    entities = ['revision', 'switchboard', 'device', 'circuit', 'terminal_device']
    default_categories = [
        ('basic', 'Základní pole', '📋', 10),
        ('additional', 'Dodatečná pole', '➕', 20),
        ('measurements', 'Měření', '📊', 30),
        ('technical', 'Technické specifikace', '🔧', 40),
        ('administrative', 'Administrativní údaje', '📄', 50),
    ]
    
    try:
        with engine.connect() as conn:
            for entity in entities:
                print_info(f"Seed kategorií pro '{entity}'...")
                for cat_key, cat_label, icon, order in default_categories:
                    try:
                        conn.execute(text("""
                            INSERT INTO field_categories 
                            (entity_type, category_key, category_label, icon, display_order)
                            VALUES (:entity, :key, :label, :icon, :order)
                            ON CONFLICT (entity_type, category_key) DO NOTHING
                        """), {
                            'entity': entity,
                            'key': cat_key,
                            'label': cat_label,
                            'icon': icon,
                            'order': order
                        })
                    except Exception as e:
                        print_warning(f"  Chyba při insertu {entity}/{cat_key}: {e}")
                
                conn.commit()
                print_success(f"Kategorie pro '{entity}' seeded")
        
        return True
    except Exception as e:
        print_error(f"Chyba při seed kategorií: {e}")
        return False

def verify_migration(engine, inspector):
    """Ověří, že migrace proběhla správně"""
    print_header("🔍 OVĚŘENÍ MIGRACE")
    
    try:
        with engine.connect() as conn:
            # Zkontroluj počet sloupců v dropdown_config
            result = conn.execute(text("""
                SELECT COUNT(*) as column_count 
                FROM information_schema.columns 
                WHERE table_name = 'dropdown_config'
            """))
            count = result.scalar()
            
            if count >= 12:
                print_success(f"dropdown_config má {count} sloupců (očekáváno: 12)")
            else:
                print_warning(f"dropdown_config má {count} sloupců (očekáváno: 12)")
            
            # Zkontroluj field_categories
            if check_table_exists(inspector, 'field_categories'):
                result = conn.execute(text("SELECT COUNT(*) FROM field_categories"))
                cat_count = result.scalar()
                print_success(f"field_categories má {cat_count} záznamů")
            else:
                print_warning("Tabulka field_categories neexistuje")
            
            print_success("\nMigrace dokončena!")
            return True
            
    except Exception as e:
        print_error(f"Chyba při ověřování: {e}")
        return False

def main():
    """Hlavní funkce - orchestrace celé migrace"""
    print_header("🚀 REVIZE APP - DATABASE MIGRATION")
    print_info("PostgreSQL Database Migration & Setup")
    print_info("Phase 4.5 - DropdownConfig + Field Categories\n")
    
    # Získej DATABASE_URL
    database_url = get_database_url()
    print_info(f"Database: {database_url.split('@')[1] if '@' in database_url else 'localhost'}\n")
    
    try:
        # Připojení k databázi
        engine = create_engine(database_url, echo=False)
        inspector = inspect(engine)
        
        # Test připojení
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print_success("Připojení k databázi úspěšné\n")
        
        # Spusť migrační kroky
        steps = [
            ("Vytváření základních tabulek", lambda: create_all_tables(engine, inspector)),
            ("Migrace dropdown_config", lambda: migrate_dropdown_config(engine, inspector)),
            ("Vytvoření field_categories", lambda: create_field_categories_table(engine, inspector)),
            ("Seed kategorií", lambda: seed_field_categories(engine)),
            ("Ověření migrace", lambda: verify_migration(engine, inspector)),
        ]
        
        all_success = True
        for step_name, step_func in steps:
            if not step_func():
                all_success = False
                print_error(f"Krok '{step_name}' selhal!")
                break
        
        if all_success:
            print_header("✅ MIGRACE ÚSPĚŠNĚ DOKONČENA")
            print_success("Databáze je připravena!")
            print_info("\nDalší kroky:")
            print_info("  1. Aplikace by měla být připravena ke spuštění")
            print_info("  2. Otestuj /settings endpoint")
            print_info("  3. Otestuj edit formuláře\n")
            return 0
        else:
            print_header("❌ MIGRACE SELHALA")
            return 1
            
    except SQLAlchemyError as e:
        print_error(f"Database error: {e}")
        return 1
    except Exception as e:
        print_error(f"Neočekávaná chyba: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
