#!/usr/bin/env python3
"""
🔧 REVIZE APP - Database Migration Script (SQLAlchemy verze)
============================================================
Automaticky vytvoří databázovou strukturu pomocí SQLAlchemy modelů.

Použití při deployment:
    python migrate_db.py

Co dělá:
    1. Vytvoří všechny tabulky z models.py
    2. Seed základních kategorií pro field_categories
    3. Seed výchozích hodnot pro dropdown_config

Bezpečnost:
    - Idempotentní (můžeš spustit vícekrát)
    - Používá SQLAlchemy modely
    - Kontroluje každý krok
"""

import os
import sys
from sqlalchemy import text, inspect
from sqlalchemy.exc import SQLAlchemyError

# Import database a modelů
from database import engine, Base, SessionLocal
from models import (
    User, Revision, Switchboard, SwitchboardMeasurement, SwitchboardDevice,
    Circuit, CircuitMeasurement, TerminalDevice, DropdownSource, 
    DropdownConfig, FieldCategory
)

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

def check_database_connection():
    """Zkontroluje připojení k databázi"""
    print_header("🔌 KONTROLA PŘIPOJENÍ")
    
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        print_error("DATABASE_URL není nastavena!")
        print_info("Nastav ji pomocí: export DATABASE_URL='postgresql://...'")
        return False
    
    # Skryj heslo v logu
    if '@' in database_url:
        display_url = database_url.split('@')[1]
    else:
        display_url = 'localhost'
    
    print_info(f"Database: {display_url}")
    
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        print_success("Připojení OK\n")
        return True
    except Exception as e:
        print_error(f"Připojení selhalo: {e}\n")
        return False

def create_all_tables():
    """Vytvoří všechny tabulky pomocí SQLAlchemy"""
    print_header("📋 VYTVÁŘENÍ TABULEK")
    
    try:
        # Vytvoř všechny tabulky z Base.metadata
        Base.metadata.create_all(bind=engine)
        print_success("Všechny tabulky úspěšně vytvořeny")
        
        # Zjisti, které tabulky byly vytvořeny
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        print_info(f"\nDostupné tabulky ({len(tables)}):")
        for table in sorted(tables):
            print_info(f"  • {table}")
        
        return True
        
    except Exception as e:
        print_error(f"Chyba při vytváření tabulek: {e}")
        return False

def seed_field_categories():
    """Seed základních kategorií pro field_categories"""
    print_header("🌱 SEED KATEGORIÍ")
    
    entities = ['revision', 'switchboard', 'device', 'circuit', 'terminal_device']
    default_categories = [
        ('basic', 'Základní pole', '📋', 10),
        ('additional', 'Dodatečná pole', '➕', 20),
        ('measurements', 'Měření', '📊', 30),
        ('technical', 'Technické specifikace', '🔧', 40),
        ('administrative', 'Administrativní údaje', '📄', 50),
    ]
    
    db = SessionLocal()
    try:
        inserted_count = 0
        skipped_count = 0
        
        for entity in entities:
            print_info(f"Seed kategorií pro '{entity}'...")
            
            for cat_key, cat_label, icon, order in default_categories:
                # Zkontroluj, zda kategorie už existuje
                existing = db.query(FieldCategory).filter(
                    FieldCategory.entity_type == entity,
                    FieldCategory.category_key == cat_key
                ).first()
                
                if not existing:
                    category = FieldCategory(
                        entity_type=entity,
                        category_key=cat_key,
                        category_label=cat_label,
                        icon=icon,
                        display_order=order
                    )
                    db.add(category)
                    inserted_count += 1
                else:
                    skipped_count += 1
            
            db.commit()
            print_success(f"✓ Kategorie pro '{entity}' seeded")
        
        print_info(f"\nVloženo {inserted_count} nových kategorií")
        if skipped_count > 0:
            print_info(f"Přeskočeno {skipped_count} existujících kategorií")
        
        return True
        
    except Exception as e:
        print_error(f"Chyba při seed kategorií: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def seed_dropdown_config():
    """Seed výchozí konfigurace pro dropdown_config"""
    print_header("🌱 SEED DROPDOWN CONFIG")
    
    # Definice všech konfigurovatelných polí
    fields_config = {
        'switchboard': [
            ('switchboard_type', 'Typ rozváděče', 'basic', 'text'),
            ('switchboard_location', 'Umístění', 'basic', 'text'),
            ('switchboard_manufacturer', 'Výrobce rozváděče', 'technical', 'text'),
            ('switchboard_ip_rating', 'Stupeň krytí (IP)', 'technical', 'text'),
            ('switchboard_impact_protection', 'Mechanická odolnost (IK)', 'technical', 'text'),
            ('switchboard_protection_class', 'Třída ochrany', 'technical', 'text'),
        ],
        'device': [
            ('switchboard_device_type', 'Typ zařízení', 'basic', 'text'),
            ('switchboard_device_manufacturer', 'Výrobce', 'technical', 'text'),
            ('switchboard_device_trip_characteristic', 'Vypínací charakteristika', 'technical', 'text'),
        ],
        'circuit': [
            ('circuit_cable', 'Typ kabelu', 'technical', 'text'),
            ('circuit_cable_installation_method', 'Způsob uložení kabelu', 'technical', 'text'),
            ('circuit_cable_termination', 'Zakončení kabelu', 'technical', 'text'),
        ],
        'terminal_device': [
            ('terminal_device_type', 'Typ koncového zařízení', 'basic', 'text'),
            ('terminal_device_manufacturer', 'Výrobce', 'technical', 'text'),
            ('terminal_device_installation_method', 'Způsob instalace', 'technical', 'text'),
        ],
    }
    
    db = SessionLocal()
    try:
        inserted_count = 0
        
        for entity_type, fields in fields_config.items():
            print_info(f"Seed konfigurace pro '{entity_type}'...")
            
            for field_name, field_label, field_category, field_type in fields:
                # Zkontroluj, zda konfigurace už existuje
                existing = db.query(DropdownConfig).filter(
                    DropdownConfig.entity_type == entity_type,
                    DropdownConfig.field_name == field_name
                ).first()
                
                if not existing:
                    config = DropdownConfig(
                        entity_type=entity_type,
                        field_name=field_name,
                        field_label=field_label,
                        field_category=field_category,
                        field_type=field_type,
                        dropdown_enabled=False,
                        enabled=True,
                        is_required=False,
                        display_order=0
                    )
                    db.add(config)
                    inserted_count += 1
        
        db.commit()
        print_success(f"✓ Vloženo {inserted_count} nových konfigurací")
        return True
        
    except Exception as e:
        print_error(f"Chyba při seed dropdown_config: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def create_default_user():
    """Vytvoří defaultního uživatele"""
    print_header("👤 VYTVÁŘENÍ VÝCHOZÍHO UŽIVATELE")
    
    db = SessionLocal()
    try:
        # Zkontroluj, zda už uživatel existuje
        existing_user = db.query(User).filter(User.user_id == 1).first()
        
        if not existing_user:
            user = User(
                user_id=1,
                username="admin",
                email="admin@revize-app.cz",
                password_hash="placeholder_hash"
            )
            db.add(user)
            db.commit()
            print_success("Vytvořen výchozí uživatel: admin (ID=1)")
        else:
            print_info("Výchozí uživatel již existuje")
        
        return True
        
    except Exception as e:
        print_error(f"Chyba při vytváření uživatele: {e}")
        db.rollback()
        return False
    finally:
        db.close()

def verify_migration():
    """Ověří, že migrace proběhla správně"""
    print_header("🔍 OVĚŘENÍ MIGRACE")
    
    inspector = inspect(engine)
    tables = inspector.get_table_names()
    
    required_tables = [
        'users', 'revisions', 'switchboards', 'switchboard_measurements',
        'switchboard_devices', 'circuits', 'circuit_measurements',
        'terminal_devices', 'dropdown_sources', 'dropdown_config',
        'field_categories'
    ]
    
    missing_tables = [t for t in required_tables if t not in tables]
    
    if missing_tables:
        print_error(f"Chybí tabulky: {', '.join(missing_tables)}")
        return False
    
    print_success(f"Všech {len(required_tables)} tabulek je k dispozici")
    
    # Zkontroluj počet kategorií
    db = SessionLocal()
    try:
        cat_count = db.query(FieldCategory).count()
        config_count = db.query(DropdownConfig).count()
        
        print_success(f"field_categories: {cat_count} záznamů")
        print_success(f"dropdown_config: {config_count} záznamů")
        
    finally:
        db.close()
    
    return True

def main():
    """Hlavní funkce - orchestrace celé migrace"""
    print_header("🚀 REVIZE APP - DATABASE MIGRATION")
    print_info("SQLAlchemy-based Database Migration")
    print_info("Verze: Phase 4.5 + Field Categories\n")
    
    try:
        # Kroky migrace
        steps = [
            ("Kontrola připojení", check_database_connection),
            ("Vytváření tabulek", create_all_tables),
            ("Seed kategorií", seed_field_categories),
            ("Seed dropdown config", seed_dropdown_config),
            ("Vytvoření výchozího uživatele", create_default_user),
            ("Ověření migrace", verify_migration),
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
            print_info("  1. Spusť aplikaci: uvicorn main:app")
            print_info("  2. Otevři /settings pro konfiguraci polí")
            print_info("  3. Začni vytvářet revize!\n")
            return 0
        else:
            print_header("❌ MIGRACE SELHALA")
            return 1
            
    except SQLAlchemyError as e:
        print_error(f"Database error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    except Exception as e:
        print_error(f"Neočekávaná chyba: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
