from fastapi import FastAPI, Request, Depends, Form
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
import os
import json
from datetime import datetime

from database import engine, get_db, Base
from models import *

# Initialize default user if not exists
def init_default_user():
    """Vytvoří defaultního uživatele pokud neexistuje"""
    db = next(get_db())
    try:
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
            print("✅ Vytvořen defaultní uživatel: admin (ID=1)")
        else:
            print("ℹ️  Defaultní uživatel již existuje")
    except Exception as e:
        print(f"⚠️  Chyba při vytváření defaultního uživatele: {e}")
        db.rollback()
    finally:
        db.close()

def fix_switchboard_order_nulls():
    """Opraví None hodnoty v switchboard_order na 0"""
    db = next(get_db())
    try:
        switchboards = db.query(Switchboard).filter(Switchboard.switchboard_order == None).all()
        if switchboards:
            for switchboard in switchboards:
                switchboard.switchboard_order = 0
            db.commit()
            print(f"✅ Opraveno {len(switchboards)} rozváděčů s None hodnotou v switchboard_order")
        else:
            print("ℹ️  Všechny rozváděče mají platnou hodnotu switchboard_order")
    except Exception as e:
        print(f"⚠️  Chyba při opravě switchboard_order: {e}")
        db.rollback()
    finally:
        db.close()

def run_database_migration():
    """Spustí database migraci při startu aplikace"""
    print("\n" + "="*70)
    print("🔧 SPOUŠTÍM DATABASE MIGRACI...")
    print("="*70)
    
    try:
        from sqlalchemy import text, inspect
        
        # 1. Vytvoř všechny tabulky (pokud neexistují)
        Base.metadata.create_all(bind=engine)
        print("✅ Tabulky vytvořeny")
        
        # 2. Přidej chybějící sloupce do dropdown_config (Phase 4 & 4.5)
        print("🔧 Kontroluji dropdown_config sloupce...")
        inspector = inspect(engine)
        
        if 'dropdown_config' in inspector.get_table_names():
            existing_columns = [col['name'] for col in inspector.get_columns('dropdown_config')]
            
            # Definice nových sloupců, které potřebujeme
            required_columns = {
                'field_label': "ALTER TABLE dropdown_config ADD COLUMN IF NOT EXISTS field_label VARCHAR(255)",
                'field_category': "ALTER TABLE dropdown_config ADD COLUMN IF NOT EXISTS field_category VARCHAR(100)",
                'display_order': "ALTER TABLE dropdown_config ADD COLUMN IF NOT EXISTS display_order INTEGER DEFAULT 0",
                'enabled': "ALTER TABLE dropdown_config ADD COLUMN IF NOT EXISTS enabled BOOLEAN DEFAULT TRUE",
                'is_required': "ALTER TABLE dropdown_config ADD COLUMN IF NOT EXISTS is_required BOOLEAN DEFAULT FALSE",
                'field_type': "ALTER TABLE dropdown_config ADD COLUMN IF NOT EXISTS field_type VARCHAR(50) DEFAULT 'text'",
                'custom_label': "ALTER TABLE dropdown_config ADD COLUMN IF NOT EXISTS custom_label VARCHAR(255)",
            }
            
            with engine.connect() as conn:
                added_count = 0
                for col_name, alter_sql in required_columns.items():
                    if col_name not in existing_columns:
                        try:
                            conn.execute(text(alter_sql))
                            conn.commit()
                            print(f"  ✅ Přidán sloupec: {col_name}")
                            added_count += 1
                        except Exception as e:
                            print(f"  ⚠️  Chyba při přidávání {col_name}: {e}")
                            conn.rollback()
                
                if added_count > 0:
                    print(f"✅ Přidáno {added_count} nových sloupců do dropdown_config")
                else:
                    print("ℹ️  Všechny sloupce již existují v dropdown_config")
        
        # 3. Seed field_categories pokud je tabulka prázdná
        db = next(get_db())
        try:
            cat_count = db.query(FieldCategory).count()
            if cat_count == 0:
                print("🌱 Seed kategorií...")
                entities = ['revision', 'switchboard', 'device', 'circuit', 'terminal_device']
                default_categories = [
                    ('basic', 'Základní pole', '📋', 10),
                    ('additional', 'Dodatečná pole', '➕', 20),
                    ('measurements', 'Měření', '📊', 30),
                    ('technical', 'Technické specifikace', '🔧', 40),
                    ('administrative', 'Administrativní údaje', '📄', 50),
                ]
                
                for entity in entities:
                    for cat_key, cat_label, icon, order in default_categories:
                        category = FieldCategory(
                            entity_type=entity,
                            category_key=cat_key,
                            category_label=cat_label,
                            icon=icon,
                            display_order=order
                        )
                        db.add(category)
                
                db.commit()
                print(f"✅ Vloženo {len(entities) * len(default_categories)} kategorií")
            else:
                print(f"ℹ️  Kategorie již existují ({cat_count} záznamů)")
                
        finally:
            db.close()
            
        print("="*70)
        print("✅ MIGRACE DOKONČENA")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"❌ CHYBA PŘI MIGRACI: {e}")
        import traceback
        traceback.print_exc()
        # Neopouštíme aplikaci - zkusíme běžet i s chybou


def run_field_config_seed(force=False):
    """
    Automatický seed konfigurace polí při startu
    Spustí se pouze pokud je dropdown_config prázdná (nebo force=True)
    """
    print("\n" + "="*70)
    print("🌱 KONTROLA FIELD CONFIG...")
    print("="*70)
    
    db = next(get_db())
    try:
        # Zkontroluj jestli už máme nějakou konfiguraci
        config_count = db.query(DropdownConfig).count()
        
        if config_count > 0 and not force:
            print(f"ℹ️  Field config již existuje ({config_count} záznamů)")
            print("="*70 + "\n")
            return
        
        if force and config_count > 0:
            print(f"⚠️  FORCE seed - smazání {config_count} existujících záznamů...")
            db.query(DropdownConfig).delete()
            db.commit()
        
        print("⚠️  Field config je prázdná, spouštím automatický seed...")
        print("")
        
        # Definice všech polí pro seed
        FIELD_CONFIGS = {
            'revision': [
                # BASIC FIELDS
                ('revision_code', 'Kód revize', 'basic', 'text', False, False, 10),
                ('revision_name', 'Název revize', 'basic', 'text', True, True, 20),
                ('revision_owner', 'Vlastník', 'basic', 'text', True, False, 30),
                ('revision_client', 'Klient', 'basic', 'text', True, False, 40),
                ('revision_address', 'Adresa', 'basic', 'textarea', True, False, 50),
                
                # ADDITIONAL FIELDS
                ('revision_description', 'Popis', 'additional', 'textarea', True, False, 100),
                ('revision_type', 'Typ revize', 'additional', 'text', True, False, 110),
                ('revision_date_of_previous_revision', 'Datum předchozí revize', 'additional', 'date', False, False, 120),
                ('revision_start_date', 'Datum zahájení', 'additional', 'date', True, False, 130),
                ('revision_end_date', 'Datum ukončení', 'additional', 'date', True, False, 140),
                ('revision_date_of_creation', 'Datum vytvoření', 'additional', 'date', True, False, 150),
                ('revision_recommended_date_for_next_revision', 'Doporučený termín další revize', 'additional', 'date', False, False, 160),
                
                # ADMINISTRATIVE FIELDS
                ('revision_number_of_copies_technician', 'Počet kopií - technik', 'administrative', 'number', False, False, 200),
                ('revision_number_of_copies_owner', 'Počet kopií - vlastník', 'administrative', 'number', False, False, 210),
                ('revision_number_of_copies_contractor', 'Počet kopií - zhotovitel', 'administrative', 'number', False, False, 220),
                ('revision_number_of_copies_client', 'Počet kopií - klient', 'administrative', 'number', False, False, 230),
                ('revision_attachment', 'Příloha', 'administrative', 'text', False, False, 240),
                ('revision_attachment_submitter', 'Odevzdavatel přílohy', 'administrative', 'text', False, False, 250),
                ('revision_attachment_producer', 'Zhotovitel přílohy', 'administrative', 'text', False, False, 260),
                ('revision_attachment_date_of_creation', 'Datum vytvoření přílohy', 'administrative', 'date', False, False, 270),
                ('revision_technician', 'Technik', 'administrative', 'text', True, False, 280),
                ('revision_certificate_number', 'Číslo osvědčení', 'administrative', 'text', False, False, 290),
                ('revision_authorization_number', 'Číslo autorizace', 'administrative', 'text', False, False, 300),
                ('revision_project_documentation', 'Projektová dokumentace', 'administrative', 'textarea', False, False, 310),
                ('revision_contractor', 'Zhotovitel', 'administrative', 'text', False, False, 320),
                ('revision_short_description', 'Krátký popis', 'administrative', 'textarea', False, False, 330),
                
                # TECHNICAL FIELDS
                ('revision_measuring_instrument_manufacturer_type', 'Výrobce/typ měřicího přístroje', 'technical', 'text', False, False, 400),
                ('revision_measuring_instrument_serial_number', 'Výrobní číslo měřicího přístroje', 'technical', 'text', False, False, 410),
                ('revision_measuring_instrument_calibration', 'Kalibrace přístroje', 'technical', 'text', False, False, 420),
                ('revision_measuring_instrument_calibration_validity', 'Platnost kalibrace', 'technical', 'date', False, False, 430),
                ('revision_overall_assessment', 'Celkové hodnocení', 'technical', 'textarea', False, False, 440),
            ],
            
            'switchboard': [
                # BASIC FIELDS
                ('switchboard_name', 'Název rozváděče', 'basic', 'text', True, True, 10),
                ('switchboard_description', 'Popis', 'basic', 'textarea', True, False, 20),
                ('switchboard_location', 'Umístění', 'basic', 'text', True, False, 30),
                ('switchboard_type', 'Typ rozváděče', 'basic', 'text', True, False, 40),
                
                # TECHNICAL FIELDS
                ('switchboard_serial_number', 'Výrobní číslo', 'technical', 'text', False, False, 100),
                ('switchboard_production_date', 'Datum výroby', 'technical', 'date', False, False, 110),
                ('switchboard_ip_rating', 'Stupeň krytí (IP)', 'technical', 'text', True, False, 120),
                ('switchboard_impact_protection', 'Mechanická odolnost (IK)', 'technical', 'text', False, False, 130),
                ('switchboard_protection_class', 'Třída ochrany', 'technical', 'text', False, False, 140),
                ('switchboard_rated_current', 'Jmenovitý proud', 'technical', 'number', True, False, 150),
                ('switchboard_rated_voltage', 'Jmenovité napětí', 'technical', 'number', True, False, 160),
                ('switchboard_manufacturer', 'Výrobce rozváděče', 'technical', 'text', True, False, 170),
                ('switchboard_manufacturer_address', 'Adresa výrobce', 'technical', 'textarea', False, False, 180),
                ('switchboard_standards', 'Normy', 'technical', 'textarea', False, False, 190),
                ('switchboard_enclosure_type', 'Typ skříně', 'technical', 'text', False, False, 200),
                ('switchboard_enclosure_manufacturer', 'Výrobce skříně', 'technical', 'text', False, False, 210),
                ('switchboard_enclosure_installation_method', 'Způsob instalace skříně', 'technical', 'text', False, False, 220),
                
                # ADDITIONAL FIELDS
                ('switchboard_superior_switchboard', 'Nadřazený rozváděč', 'additional', 'text', False, False, 300),
                ('switchboard_superior_circuit_breaker_rated_current', 'Jmenovitý proud nadřazeného jističe', 'additional', 'number', False, False, 310),
                ('switchboard_superior_circuit_breaker_trip_characteristic', 'Vypínací charakteristika nadřazeného jističe', 'additional', 'text', False, False, 320),
                ('switchboard_superior_circuit_breaker_manufacturer', 'Výrobce nadřazeného jističe', 'additional', 'text', False, False, 330),
                ('switchboard_superior_circuit_breaker_model', 'Model nadřazeného jističe', 'additional', 'text', False, False, 340),
                ('switchboard_main_switch', 'Hlavní vypínač', 'additional', 'text', False, False, 350),
                ('switchboard_note', 'Poznámka', 'additional', 'textarea', False, False, 360),
                ('switchboard_cable', 'Typ kabelu', 'additional', 'text', True, False, 370),
                ('switchboard_cable_installation_method', 'Způsob uložení kabelu', 'additional', 'text', False, False, 380),
                
                # MEASUREMENTS
                ('measurements_switchboard_insulation_resistance', 'Izolační odpor', 'measurements', 'number', False, False, 500),
                ('measurements_switchboard_loop_impedance_min', 'Smyčková impedance min', 'measurements', 'number', False, False, 510),
                ('measurements_switchboard_loop_impedance_max', 'Smyčková impedance max', 'measurements', 'number', False, False, 520),
                ('measurements_switchboard_rcd_trip_time_ms', 'Doba vypnutí RCD (ms)', 'measurements', 'number', False, False, 530),
                ('measurements_switchboard_rcd_test_current_ma', 'Zkušební proud RCD (mA)', 'measurements', 'number', False, False, 540),
                ('measurements_switchboard_earth_resistance', 'Odpor uzemnění', 'measurements', 'number', False, False, 550),
            ],
            
            'device': [
                # BASIC FIELDS
                ('switchboard_device_position', 'Pozice', 'basic', 'text', True, False, 10),
                ('switchboard_device_type', 'Typ zařízení', 'basic', 'text', True, True, 20),
                ('switchboard_device_manufacturer', 'Výrobce', 'basic', 'text', True, False, 30),
                ('switchboard_device_model', 'Model', 'basic', 'text', True, False, 40),
                
                # TECHNICAL FIELDS
                ('switchboard_device_trip_characteristic', 'Vypínací charakteristika', 'technical', 'text', True, False, 100),
                ('switchboard_device_rated_current', 'Jmenovitý proud', 'technical', 'number', True, False, 110),
                ('switchboard_device_residual_current_ma', 'Rozdílový proud (mA)', 'technical', 'number', False, False, 120),
                ('switchboard_device_poles', 'Počet pólů', 'technical', 'number', False, False, 130),
                ('switchboard_device_module_width', 'Šířka modulu', 'technical', 'number', False, False, 140),
                
                # ADDITIONAL FIELDS
                ('switchboard_device_sub_devices', 'Podřízená zařízení', 'additional', 'textarea', False, False, 200),
            ],
            
            'circuit': [
                # BASIC FIELDS
                ('circuit_number', 'Číslo obvodu', 'basic', 'text', True, False, 10),
                ('circuit_room', 'Místnost', 'basic', 'text', True, False, 20),
                ('circuit_description', 'Popis', 'basic', 'textarea', True, False, 30),
                
                # ADDITIONAL FIELDS
                ('circuit_description_from_switchboard', 'Popis z rozváděče', 'additional', 'textarea', False, False, 100),
                ('circuit_number_of_outlets', 'Počet zásuvek', 'additional', 'number', False, False, 110),
                ('circuit_cable_termination', 'Zakončení kabelu', 'additional', 'text', False, False, 120),
                ('circuit_cable', 'Typ kabelu', 'additional', 'text', True, False, 130),
                ('circuit_cable_installation_method', 'Způsob uložení kabelu', 'additional', 'text', False, False, 140),
                
                # MEASUREMENTS
                ('measurements_circuit_insulation_resistance', 'Izolační odpor', 'measurements', 'number', False, False, 200),
                ('measurements_circuit_loop_impedance_min', 'Smyčková impedance min', 'measurements', 'number', False, False, 210),
                ('measurements_circuit_loop_impedance_max', 'Smyčková impedance max', 'measurements', 'number', False, False, 220),
                ('measurements_circuit_rcd_trip_time_ms', 'Doba vypnutí RCD (ms)', 'measurements', 'number', False, False, 230),
                ('measurements_circuit_rcd_test_current_ma', 'Zkušební proud RCD (mA)', 'measurements', 'number', False, False, 240),
                ('measurements_circuit_earth_resistance', 'Odpor uzemnění', 'measurements', 'number', False, False, 250),
                ('measurements_circuit_continuity', 'Kontinuita', 'measurements', 'number', False, False, 260),
                ('measurements_circuit_order_of_phases', 'Pořadí fází', 'measurements', 'text', False, False, 270),
            ],
            
            'terminal_device': [
                # BASIC FIELDS
                ('terminal_device_type', 'Typ koncového zařízení', 'basic', 'text', True, True, 10),
                ('terminal_device_manufacturer', 'Výrobce', 'basic', 'text', False, False, 20),
                ('terminal_device_model', 'Model', 'basic', 'text', False, False, 30),
                
                # TECHNICAL FIELDS
                ('terminal_device_marking', 'Označení', 'technical', 'text', False, False, 100),
                ('terminal_device_power', 'Výkon', 'technical', 'number', False, False, 110),
                ('terminal_device_ip_rating', 'Stupeň krytí (IP)', 'technical', 'text', False, False, 120),
                ('terminal_device_protection_class', 'Třída ochrany', 'technical', 'text', False, False, 130),
                ('terminal_device_serial_number', 'Výrobní číslo', 'technical', 'text', False, False, 140),
                ('terminal_device_supply_type', 'Typ napájení', 'technical', 'text', False, False, 150),
                ('terminal_device_installation_method', 'Způsob instalace', 'technical', 'text', False, False, 160),
            ],
        }
        
        # Seed všechna pole
        total_inserted = 0
        for entity_type, fields in FIELD_CONFIGS.items():
            print(f"  Seeding {entity_type}...")
            
            for field_name, field_label, category, field_type, enabled, required, display_order in fields:
                config = DropdownConfig(
                    entity_type=entity_type,
                    field_name=field_name,
                    field_label=field_label,
                    field_category=category,
                    field_type=field_type,
                    enabled=enabled,
                    is_required=required,
                    display_order=display_order,
                    dropdown_enabled=False,
                    dropdown_category=None
                )
                db.add(config)
                total_inserted += 1
            
            db.commit()
        
        print(f"\n✅ Seed dokončen: {total_inserted} polí nakonfigurováno")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"❌ CHYBA PŘI SEED: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
    finally:
        db.close()


# Initialize FastAPI app
app = FastAPI(title="Revize App")

# Create default user on startup
@app.on_event("startup")
async def startup_event():
    run_database_migration()     # 1. Migrace tabulek
    run_field_config_seed()       # 2. AUTO SEED konfigurace polí ← NOVĚ!
    init_default_user()           # 3. Výchozí uživatel
    fix_switchboard_order_nulls() # 4. Opravy


# Add session middleware
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Setup templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set default user (for now, without authentication)
def get_current_user(request: Request):
    """Get current user from session. For now, returns default user_id=1"""
    user_id = request.session.get("user_id", 1)
    return user_id


# Define which fields can have dropdowns for each entity
def get_dropdown_configurable_fields():
    """Returns dictionary of entities and their dropdown-configurable fields"""
    return {
        "switchboard": {
            "switchboard_type": "Typ rozváděče",
            "switchboard_ip_rating": "Stupeň krytí (IP)",
            "switchboard_impact_protection": "Mechanická odolnost (IK)",
            "switchboard_protection_class": "Třída ochrany",
            "switchboard_manufacturer": "Výrobce rozváděče",
            "switchboard_enclosure_manufacturer": "Výrobce skříně",
            "switchboard_enclosure_installation_method": "Způsob instalace skříně",
            "switchboard_superior_circuit_breaker_trip_characteristic": "Vypínací charakteristika nadřazeného jističe",
            "switchboard_superior_circuit_breaker_manufacturer": "Výrobce nadřazeného jističe",
            "switchboard_cable": "Typ kabelu",
            "switchboard_cable_installation_method": "Způsob uložení kabelu",
        },
        "device": {
            "switchboard_device_type": "Typ přístroje",
            "switchboard_device_manufacturer": "Výrobce přístroje",
            "switchboard_device_trip_characteristic": "Vypínací charakteristika",
        },
        "circuit": {
            "circuit_cable": "Typ kabelu",
            "circuit_cable_installation_method": "Způsob uložení kabelu",
        },
        "terminal_device": {
            "terminal_device_type": "Typ koncového zařízení",
            "terminal_device_manufacturer": "Výrobce koncového zařízení",
            "terminal_device_ip_rating": "Stupeň krytí (IP)",
            "terminal_device_protection_class": "Třída ochrany",
            "terminal_device_installation_method": "Způsob instalace",
        },
    }


def get_field_dropdown_config(entity_type: str, db: Session):
    """Get dropdown configuration for all fields of an entity type
    
    Returns:
        dict: {field_name: {'enabled': bool, 'category': str or None}}
    """
    configs = db.query(DropdownConfig).filter(
        DropdownConfig.entity_type == entity_type
    ).all()
    
    result = {}
    for config in configs:
        result[config.field_name] = {
            'enabled': config.dropdown_enabled,
            'category': config.dropdown_category
        }
    
    return result


def get_entity_field_config(entity_type: str, db: Session):
    """
    PHASE 4: Get field configuration for an entity
    PHASE 4.5: Includes custom_label for field renaming
    Returns list of enabled fields with their configurations
    
    Returns:
        list: [{'name': str, 'label': str, 'type': str, 'required': bool, ...}, ...]
    """
    fields = db.query(DropdownConfig).filter(
        DropdownConfig.entity_type == entity_type,
        DropdownConfig.enabled == True
    ).order_by(DropdownConfig.display_order).all()
    
    # 🔍 DEBUG: Check for dropdowns
    dropdown_count = sum(1 for f in fields if f.dropdown_enabled and f.dropdown_category)
    print(f"🔍 DEBUG get_entity_field_config({entity_type}): "
          f"{len(fields)} viditelných polí, {dropdown_count} s dropdownem")
    
    result = []
    for field in fields:
        # PHASE 4.5: Use custom_label if set, otherwise use field_label
        display_label = field.custom_label if field.custom_label else field.field_label
        
        # 🔍 DEBUG: Log dropdown fields
        if field.dropdown_enabled:
            status = f"✅ kategorie: {field.dropdown_category}" if field.dropdown_category else "⚠️  BEZ kategorie"
            print(f"  - {field.field_name}: dropdown {status}")
        
        result.append({
            'name': field.field_name,
            'label': display_label,
            'type': field.field_type,
            'required': field.is_required,
            'category': field.field_category,
            'has_dropdown': field.dropdown_enabled,
            'dropdown_category': field.dropdown_category
        })
    
    return result


def get_sidebar_revisions(db: Session, user_id: int):
    """Helper function to get revisions for sidebar"""
    return db.query(Revision).filter(
        Revision.user_id == user_id
    ).order_by(Revision.revision_date_of_creation.desc()).limit(5).all()


# Root endpoint - Dashboard
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Fetch user's revisions with eager loading for sidebar
    revisions = db.query(Revision).filter(Revision.user_id == user_id).order_by(Revision.revision_date_of_creation.desc()).all()
    
    # Calculate statistics
    total_revisions = len(revisions)
    active_revisions = sum(1 for r in revisions if r.revision_end_date is None)
    completed_revisions = sum(1 for r in revisions if r.revision_end_date is not None)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user_id": user_id,
        "revisions": revisions,
        "total_revisions": total_revisions,
        "active_revisions": active_revisions,
        "completed_revisions": completed_revisions,
        "sidebar_revisions": get_sidebar_revisions(db, user_id)
    })


# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}


# REVISION CRUD ENDPOINTS

# Create - Show form
@app.get("/revision/create", response_class=HTMLResponse)
async def revision_create_form(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Get dropdown configuration for revision
    dropdown_config = get_field_dropdown_config("revision", db)
    
    # PHASE 4: Get field configuration
    field_configs = get_entity_field_config('revision', db)
    
    # Get all dropdown sources grouped by category
    categories = db.query(DropdownSource.category).distinct().all()
    dropdown_sources = {}
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    return templates.TemplateResponse("revision_form.html", {
        "request": request,
        "user_id": user_id,
        "revision": None,
        "dropdown_config": dropdown_config,
        "dropdown_sources": dropdown_sources,
        "field_configs": field_configs
    })


# Create - Save new revision
@app.post("/revision/create")
async def revision_create(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    form_data = await request.form()
    
    # Helper function to convert empty strings to None
    def get_value(key, convert_type=None):
        value = form_data.get(key, "").strip()
        if not value:
            return None
        if convert_type == int:
            return int(value) if value else None
        if convert_type == float:
            return float(value) if value else None
        return value
    
    # Create new revision
    new_revision = Revision(
        user_id=user_id,
        revision_code=get_value("revision_code"),
        revision_name=get_value("revision_name"),
        revision_owner=get_value("revision_owner"),
        revision_client=get_value("revision_client"),
        revision_address=get_value("revision_address"),
        revision_description=get_value("revision_description"),
        revision_type=get_value("revision_type"),
        revision_date_of_previous_revision=get_value("revision_date_of_previous_revision"),
        revision_start_date=get_value("revision_start_date"),
        revision_end_date=get_value("revision_end_date"),
        revision_date_of_creation=get_value("revision_date_of_creation"),
        revision_recommended_date_for_next_revision=get_value("revision_recommended_date_for_next_revision"),
        revision_number_of_copies_technician=get_value("revision_number_of_copies_technician", int),
        revision_number_of_copies_owner=get_value("revision_number_of_copies_owner", int),
        revision_number_of_copies_contractor=get_value("revision_number_of_copies_contractor", int),
        revision_number_of_copies_client=get_value("revision_number_of_copies_client", int),
        revision_attachment=get_value("revision_attachment"),
        revision_attachment_submitter=get_value("revision_attachment_submitter"),
        revision_attachment_producer=get_value("revision_attachment_producer"),
        revision_attachment_date_of_creation=get_value("revision_attachment_date_of_creation"),
        revision_technician=get_value("revision_technician"),
        revision_certificate_number=get_value("revision_certificate_number"),
        revision_authorization_number=get_value("revision_authorization_number"),
        revision_project_documentation=get_value("revision_project_documentation"),
        revision_contractor=get_value("revision_contractor"),
        revision_short_description=get_value("revision_short_description"),
        revision_measuring_instrument_manufacturer_type=get_value("revision_measuring_instrument_manufacturer_type"),
        revision_measuring_instrument_serial_number=get_value("revision_measuring_instrument_serial_number"),
        revision_measuring_instrument_calibration=get_value("revision_measuring_instrument_calibration"),
        revision_measuring_instrument_calibration_validity=get_value("revision_measuring_instrument_calibration_validity"),
        revision_overall_assessment=get_value("revision_overall_assessment")
    )
    
    db.add(new_revision)
    db.commit()
    db.refresh(new_revision)
    
    # Redirect to revision detail
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/revision/{new_revision.revision_id}", status_code=303)


# Read - Show detail (NEW CARD-BASED VERSION)
@app.get("/revision/{revision_id}", response_class=HTMLResponse)
async def revision_detail(revision_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    revision = db.query(Revision).filter(
        Revision.revision_id == revision_id,
        Revision.user_id == user_id
    ).first()
    
    if not revision:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    return templates.TemplateResponse("revision_detail_redesigned.html", {
        "request": request,
        "user_id": user_id,
        "revision": revision,
        "sidebar_revisions": get_sidebar_revisions(db, user_id),
        "current_revision_for_sidebar": revision
    })


# PHASE 5: Card-based detail views - Get static card view
@app.get("/revision/{revision_id}/card/{card_type}", response_class=HTMLResponse)
async def get_revision_card(revision_id: int, card_type: str, request: Request, db: Session = Depends(get_db)):
    """Return static view of a specific card"""
    user_id = get_current_user(request)
    revision = db.query(Revision).filter(
        Revision.revision_id == revision_id,
        Revision.user_id == user_id
    ).first()
    
    if not revision:
        return HTMLResponse(content="<div class='p-4 text-red-500'>Revize nenalezena</div>", status_code=404)
    
    template_name = f"cards/revision_static_{card_type}.html"
    return templates.TemplateResponse(template_name, {
        "request": request,
        "revision": revision
    })


# PHASE 5: Get edit form for card
@app.get("/revision/{revision_id}/edit-card/{card_type}", response_class=HTMLResponse)
async def get_revision_card_edit(revision_id: int, card_type: str, request: Request, db: Session = Depends(get_db)):
    """Return edit form for a specific card"""
    user_id = get_current_user(request)
    revision = db.query(Revision).filter(
        Revision.revision_id == revision_id,
        Revision.user_id == user_id
    ).first()
    
    if not revision:
        return HTMLResponse(content="<div class='p-4 text-red-500'>Revize nenalezena</div>", status_code=404)
    
    # 🔧 BUGFIX: Add field configs and dropdown sources for dynamic rendering
    field_configs = get_entity_field_config('revision', db)
    
    # Get all dropdown sources grouped by category
    categories = db.query(DropdownSource.category).distinct().all()
    dropdown_sources = {}
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    template_name = f"cards/revision_edit_{card_type}.html"
    return templates.TemplateResponse(template_name, {
        "request": request,
        "revision": revision,
        "field_configs": field_configs,
        "dropdown_sources": dropdown_sources
    })


# PHASE 5: Update card data
@app.post("/revision/{revision_id}/update-card/{card_type}", response_class=HTMLResponse)
async def update_revision_card(revision_id: int, card_type: str, request: Request, db: Session = Depends(get_db)):
    """Update card data and return static view"""
    user_id = get_current_user(request)
    revision = db.query(Revision).filter(
        Revision.revision_id == revision_id,
        Revision.user_id == user_id
    ).first()
    
    if not revision:
        return HTMLResponse(content="<div class='p-4 text-red-500'>Revize nenalezena</div>", status_code=404)
    
    form_data = await request.form()
    
    # Helper function to convert empty strings to None
    def get_value(key, convert_type=None):
        value = form_data.get(key, "").strip()
        if not value:
            return None
        if convert_type == int:
            return int(value) if value else None
        if convert_type == float:
            return float(value) if value else None
        return value
    
    # Update fields based on card type
    if card_type == 'basic':
        revision.revision_name = get_value("revision_name")
        revision.revision_owner = get_value("revision_owner")
        revision.revision_client = get_value("revision_client")
        revision.revision_address = get_value("revision_address")
        revision.revision_type = get_value("revision_type")
        revision.revision_description = get_value("revision_description")
        revision.revision_short_description = get_value("revision_short_description")
    
    elif card_type == 'dates':
        revision.revision_date_of_creation = get_value("revision_date_of_creation")
        revision.revision_start_date = get_value("revision_start_date")
        revision.revision_end_date = get_value("revision_end_date")
        revision.revision_date_of_previous_revision = get_value("revision_date_of_previous_revision")
        revision.revision_recommended_date_for_next_revision = get_value("revision_recommended_date_for_next_revision")
    
    elif card_type == 'admin':
        revision.revision_code = get_value("revision_code")
        revision.ico = get_value("ico")
        revision.draftsman = get_value("draftsman")
        revision.project_documentation_number = get_value("project_documentation_number")
        revision.contract_number = get_value("contract_number")
        revision.order_number = get_value("order_number")
        revision.revision_notes = get_value("revision_notes")
        revision.revision_project_documentation = get_value("revision_project_documentation")
        revision.revision_overall_assessment = get_value("revision_overall_assessment")
    
    db.commit()
    
    # Return static view
    template_name = f"cards/revision_static_{card_type}.html"
    return templates.TemplateResponse(template_name, {
        "request": request,
        "revision": revision
    })


# Update - Show edit form
@app.get("/revision/{revision_id}/edit", response_class=HTMLResponse)
async def revision_edit_form(revision_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    revision = db.query(Revision).filter(
        Revision.revision_id == revision_id,
        Revision.user_id == user_id
    ).first()
    
    if not revision:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    # Get dropdown configuration for revision
    dropdown_config = get_field_dropdown_config("revision", db)
    
    # PHASE 4: Get field configuration
    field_configs = get_entity_field_config('revision', db)
    
    # Get all dropdown sources grouped by category
    categories = db.query(DropdownSource.category).distinct().all()
    dropdown_sources = {}
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    return templates.TemplateResponse("revision_form.html", {
        "request": request,
        "user_id": user_id,
        "revision": revision,
        "dropdown_config": dropdown_config,
        "dropdown_sources": dropdown_sources,
        "field_configs": field_configs
    })


# Update - Save changes
@app.post("/revision/{revision_id}/update")
async def revision_update(revision_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    revision = db.query(Revision).filter(
        Revision.revision_id == revision_id,
        Revision.user_id == user_id
    ).first()
    
    if not revision:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    form_data = await request.form()
    
    # Helper function to convert empty strings to None
    def get_value(key, convert_type=None):
        value = form_data.get(key, "").strip()
        if not value:
            return None
        if convert_type == int:
            return int(value) if value else None
        if convert_type == float:
            return float(value) if value else None
        return value
    
    # Update revision fields
    revision.revision_code = get_value("revision_code")
    revision.revision_name = get_value("revision_name")
    revision.revision_owner = get_value("revision_owner")
    revision.revision_client = get_value("revision_client")
    revision.revision_address = get_value("revision_address")
    revision.revision_description = get_value("revision_description")
    revision.revision_type = get_value("revision_type")
    revision.revision_date_of_previous_revision = get_value("revision_date_of_previous_revision")
    revision.revision_start_date = get_value("revision_start_date")
    revision.revision_end_date = get_value("revision_end_date")
    revision.revision_date_of_creation = get_value("revision_date_of_creation")
    revision.revision_recommended_date_for_next_revision = get_value("revision_recommended_date_for_next_revision")
    revision.revision_number_of_copies_technician = get_value("revision_number_of_copies_technician", int)
    revision.revision_number_of_copies_owner = get_value("revision_number_of_copies_owner", int)
    revision.revision_number_of_copies_contractor = get_value("revision_number_of_copies_contractor", int)
    revision.revision_number_of_copies_client = get_value("revision_number_of_copies_client", int)
    revision.revision_attachment = get_value("revision_attachment")
    revision.revision_attachment_submitter = get_value("revision_attachment_submitter")
    revision.revision_attachment_producer = get_value("revision_attachment_producer")
    revision.revision_attachment_date_of_creation = get_value("revision_attachment_date_of_creation")
    revision.revision_technician = get_value("revision_technician")
    revision.revision_certificate_number = get_value("revision_certificate_number")
    revision.revision_authorization_number = get_value("revision_authorization_number")
    revision.revision_project_documentation = get_value("revision_project_documentation")
    revision.revision_contractor = get_value("revision_contractor")
    revision.revision_short_description = get_value("revision_short_description")
    revision.revision_measuring_instrument_manufacturer_type = get_value("revision_measuring_instrument_manufacturer_type")
    revision.revision_measuring_instrument_serial_number = get_value("revision_measuring_instrument_serial_number")
    revision.revision_measuring_instrument_calibration = get_value("revision_measuring_instrument_calibration")
    revision.revision_measuring_instrument_calibration_validity = get_value("revision_measuring_instrument_calibration_validity")
    revision.revision_overall_assessment = get_value("revision_overall_assessment")
    
    db.commit()
    
    # Redirect to revision detail
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/revision/{revision_id}", status_code=303)


# Delete
@app.post("/revision/{revision_id}/delete")
async def revision_delete(revision_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    revision = db.query(Revision).filter(
        Revision.revision_id == revision_id,
        Revision.user_id == user_id
    ).first()
    
    if revision:
        db.delete(revision)
        db.commit()
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=303)


# Duplicate
@app.post("/revision/{revision_id}/duplicate")
async def revision_duplicate(revision_id: int, request: Request, db: Session = Depends(get_db)):
    from datetime import date
    from fastapi.responses import RedirectResponse
    
    user_id = get_current_user(request)
    original = db.query(Revision).filter(
        Revision.revision_id == revision_id,
        Revision.user_id == user_id
    ).first()
    
    if not original:
        return RedirectResponse(url="/", status_code=303)
    
    # Create new revision
    new_revision = Revision(
        user_id=user_id,
        revision_code=f"{original.revision_code or ''} (kopie)" if original.revision_code else "Kopie",
        revision_name=f"{original.revision_name or ''} (kopie)" if original.revision_name else "Kopie",
        revision_owner=original.revision_owner,
        revision_client=original.revision_client,
        revision_address=original.revision_address,
        revision_description=original.revision_description,
        revision_type=original.revision_type,
        revision_date_of_previous_revision=original.revision_date_of_previous_revision,
        revision_start_date=date.today(),
        revision_end_date=None,
        revision_date_of_creation=date.today(),
        revision_recommended_date_for_next_revision=original.revision_recommended_date_for_next_revision,
        revision_number_of_copies_technician=original.revision_number_of_copies_technician,
        revision_number_of_copies_owner=original.revision_number_of_copies_owner,
        revision_number_of_copies_contractor=original.revision_number_of_copies_contractor,
        revision_number_of_copies_client=original.revision_number_of_copies_client,
        revision_attachment=original.revision_attachment,
        revision_attachment_submitter=original.revision_attachment_submitter,
        revision_attachment_producer=original.revision_attachment_producer,
        revision_attachment_date_of_creation=original.revision_attachment_date_of_creation,
        revision_technician=original.revision_technician,
        revision_certificate_number=original.revision_certificate_number,
        revision_authorization_number=original.revision_authorization_number,
        revision_project_documentation=original.revision_project_documentation,
        revision_contractor=original.revision_contractor,
        revision_short_description=original.revision_short_description,
        revision_measuring_instrument_manufacturer_type=original.revision_measuring_instrument_manufacturer_type,
        revision_measuring_instrument_serial_number=original.revision_measuring_instrument_serial_number,
        revision_measuring_instrument_calibration=original.revision_measuring_instrument_calibration,
        revision_measuring_instrument_calibration_validity=original.revision_measuring_instrument_calibration_validity,
        revision_overall_assessment=original.revision_overall_assessment
    )
    db.add(new_revision)
    db.flush()
    
    # Duplicate all switchboards with their full hierarchy
    for switchboard in original.switchboards:
        new_switchboard = Switchboard(
            revision_id=new_revision.revision_id,
            switchboard_name=switchboard.switchboard_name,
            switchboard_description=switchboard.switchboard_description,
            switchboard_location=switchboard.switchboard_location,
            switchboard_order=switchboard.switchboard_order,
            switchboard_type=switchboard.switchboard_type,
            switchboard_serial_number=switchboard.switchboard_serial_number,
            switchboard_production_date=switchboard.switchboard_production_date,
            switchboard_ip_rating=switchboard.switchboard_ip_rating,
            switchboard_impact_protection=switchboard.switchboard_impact_protection,
            switchboard_protection_class=switchboard.switchboard_protection_class,
            switchboard_rated_current=switchboard.switchboard_rated_current,
            switchboard_rated_voltage=switchboard.switchboard_rated_voltage,
            switchboard_manufacturer=switchboard.switchboard_manufacturer,
            switchboard_manufacturer_address=switchboard.switchboard_manufacturer_address,
            switchboard_standards=switchboard.switchboard_standards,
            switchboard_enclosure_type=switchboard.switchboard_enclosure_type,
            switchboard_enclosure_manufacturer=switchboard.switchboard_enclosure_manufacturer,
            switchboard_enclosure_installation_method=switchboard.switchboard_enclosure_installation_method,
            switchboard_superior_switchboard=switchboard.switchboard_superior_switchboard,
            switchboard_superior_circuit_breaker_rated_current=switchboard.switchboard_superior_circuit_breaker_rated_current,
            switchboard_superior_circuit_breaker_trip_characteristic=switchboard.switchboard_superior_circuit_breaker_trip_characteristic,
            switchboard_superior_circuit_breaker_manufacturer=switchboard.switchboard_superior_circuit_breaker_manufacturer,
            switchboard_superior_circuit_breaker_model=switchboard.switchboard_superior_circuit_breaker_model,
            switchboard_main_switch=switchboard.switchboard_main_switch,
            switchboard_note=switchboard.switchboard_note,
            switchboard_cable=switchboard.switchboard_cable,
            switchboard_cable_installation_method=switchboard.switchboard_cable_installation_method
        )
        db.add(new_switchboard)
        db.flush()
        
        # Duplicate measurements
        if switchboard.measurements:
            new_measurement = SwitchboardMeasurement(
                switchboard_id=new_switchboard.switchboard_id,
                measurements_switchboard_insulation_resistance=switchboard.measurements.measurements_switchboard_insulation_resistance,
                measurements_switchboard_loop_impedance_min=switchboard.measurements.measurements_switchboard_loop_impedance_min,
                measurements_switchboard_loop_impedance_max=switchboard.measurements.measurements_switchboard_loop_impedance_max,
                measurements_switchboard_rcd_trip_time_ms=switchboard.measurements.measurements_switchboard_rcd_trip_time_ms,
                measurements_switchboard_rcd_test_current_ma=switchboard.measurements.measurements_switchboard_rcd_test_current_ma,
                measurements_switchboard_earth_resistance=switchboard.measurements.measurements_switchboard_earth_resistance
            )
            db.add(new_measurement)
        
        # Duplicate devices (need to track old_id -> new_id for parent relationships)
        device_id_map = {}
        devices_to_process = [d for d in switchboard.devices if d.parent_device_id is None]
        
        while devices_to_process:
            device = devices_to_process.pop(0)
            new_device = SwitchboardDevice(
                switchboard_id=new_switchboard.switchboard_id,
                parent_device_id=device_id_map.get(device.parent_device_id),
                switchboard_device_position=device.switchboard_device_position,
                switchboard_device_type=device.switchboard_device_type,
                switchboard_device_manufacturer=device.switchboard_device_manufacturer,
                switchboard_device_model=device.switchboard_device_model,
                switchboard_device_trip_characteristic=device.switchboard_device_trip_characteristic,
                switchboard_device_rated_current=device.switchboard_device_rated_current,
                switchboard_device_residual_current_ma=device.switchboard_device_residual_current_ma,
                switchboard_device_sub_devices=device.switchboard_device_sub_devices,
                switchboard_device_poles=device.switchboard_device_poles,
                switchboard_device_module_width=device.switchboard_device_module_width
            )
            db.add(new_device)
            db.flush()
            device_id_map[device.device_id] = new_device.device_id
            
            # Duplicate circuits
            for circuit in device.circuits:
                new_circuit = Circuit(
                    device_id=new_device.device_id,
                    circuit_number=circuit.circuit_number,
                    circuit_room=circuit.circuit_room,
                    circuit_description=circuit.circuit_description,
                    circuit_description_from_switchboard=circuit.circuit_description_from_switchboard,
                    circuit_number_of_outlets=circuit.circuit_number_of_outlets,
                    circuit_cable_termination=circuit.circuit_cable_termination,
                    circuit_cable=circuit.circuit_cable,
                    circuit_cable_installation_method=circuit.circuit_cable_installation_method
                )
                db.add(new_circuit)
                db.flush()
                
                # Duplicate circuit measurements
                if circuit.measurements:
                    new_circuit_measurement = CircuitMeasurement(
                        circuit_id=new_circuit.circuit_id,
                        measurements_circuit_insulation_resistance=circuit.measurements.measurements_circuit_insulation_resistance,
                        measurements_circuit_loop_impedance_min=circuit.measurements.measurements_circuit_loop_impedance_min,
                        measurements_circuit_loop_impedance_max=circuit.measurements.measurements_circuit_loop_impedance_max,
                        measurements_circuit_rcd_trip_time_ms=circuit.measurements.measurements_circuit_rcd_trip_time_ms,
                        measurements_circuit_rcd_test_current_ma=circuit.measurements.measurements_circuit_rcd_test_current_ma,
                        measurements_circuit_earth_resistance=circuit.measurements.measurements_circuit_earth_resistance,
                        measurements_circuit_continuity=circuit.measurements.measurements_circuit_continuity,
                        measurements_circuit_order_of_phases=circuit.measurements.measurements_circuit_order_of_phases
                    )
                    db.add(new_circuit_measurement)
                
                # Duplicate terminal devices
                for terminal in circuit.terminal_devices:
                    new_terminal = TerminalDevice(
                        circuit_id=new_circuit.circuit_id,
                        terminal_device_type=terminal.terminal_device_type,
                        terminal_device_manufacturer=terminal.terminal_device_manufacturer,
                        terminal_device_model=terminal.terminal_device_model,
                        terminal_device_marking=terminal.terminal_device_marking,
                        terminal_device_power=terminal.terminal_device_power,
                        terminal_device_ip_rating=terminal.terminal_device_ip_rating,
                        terminal_device_protection_class=terminal.terminal_device_protection_class,
                        terminal_device_serial_number=terminal.terminal_device_serial_number,
                        terminal_device_supply_type=terminal.terminal_device_supply_type,
                        terminal_device_installation_method=terminal.terminal_device_installation_method
                    )
                    db.add(new_terminal)
            
            # Add child devices to process
            for child in device.child_devices:
                devices_to_process.append(child)
    
    db.commit()
    return RedirectResponse(url=f"/revision/{new_revision.revision_id}", status_code=303)


# SWITCHBOARD CRUD ENDPOINTS

# Create - Show form
@app.get("/revision/{revision_id}/switchboard/create", response_class=HTMLResponse)
async def switchboard_create_form(revision_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    revision = db.query(Revision).filter(
        Revision.revision_id == revision_id,
        Revision.user_id == user_id
    ).first()
    
    if not revision:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    # Get dropdown configuration for switchboard
    dropdown_config = get_field_dropdown_config("switchboard", db)
    
    # PHASE 4: Get field configuration
    field_configs = get_entity_field_config('switchboard', db)
    
    # Get all dropdown sources grouped by category
    categories = db.query(DropdownSource.category).distinct().all()
    dropdown_sources = {}
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    return templates.TemplateResponse("switchboard_form.html", {
        "request": request,
        "user_id": user_id,
        "revision": revision,
        "switchboard": None,
        "dropdown_config": dropdown_config,
        "dropdown_sources": dropdown_sources,
        "field_configs": field_configs
    })


# Create - Save new switchboard
@app.post("/revision/{revision_id}/switchboard/create")
async def switchboard_create(revision_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    revision = db.query(Revision).filter(
        Revision.revision_id == revision_id,
        Revision.user_id == user_id
    ).first()
    
    if not revision:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    form_data = await request.form()
    
    # Helper function
    def get_value(key, convert_type=None):
        value = form_data.get(key, "").strip()
        if not value:
            return None
        if convert_type == int:
            return int(value) if value else None
        if convert_type == float:
            return float(value) if value else None
        return value
    
    # Create new switchboard
    new_switchboard = Switchboard(
        revision_id=revision_id,
        switchboard_name=get_value("switchboard_name"),
        switchboard_description=get_value("switchboard_description"),
        switchboard_location=get_value("switchboard_location"),
        switchboard_order=get_value("switchboard_order", int),
        switchboard_type=get_value("switchboard_type"),
        switchboard_serial_number=get_value("switchboard_serial_number"),
        switchboard_production_date=get_value("switchboard_production_date"),
        switchboard_ip_rating=get_value("switchboard_ip_rating"),
        switchboard_impact_protection=get_value("switchboard_impact_protection"),
        switchboard_protection_class=get_value("switchboard_protection_class"),
        switchboard_rated_current=get_value("switchboard_rated_current", float),
        switchboard_rated_voltage=get_value("switchboard_rated_voltage", float),
        switchboard_manufacturer=get_value("switchboard_manufacturer"),
        switchboard_manufacturer_address=get_value("switchboard_manufacturer_address"),
        switchboard_standards=get_value("switchboard_standards"),
        switchboard_enclosure_type=get_value("switchboard_enclosure_type"),
        switchboard_enclosure_manufacturer=get_value("switchboard_enclosure_manufacturer"),
        switchboard_enclosure_installation_method=get_value("switchboard_enclosure_installation_method"),
        switchboard_superior_switchboard=get_value("switchboard_superior_switchboard"),
        switchboard_superior_circuit_breaker_rated_current=get_value("switchboard_superior_circuit_breaker_rated_current", float),
        switchboard_superior_circuit_breaker_trip_characteristic=get_value("switchboard_superior_circuit_breaker_trip_characteristic"),
        switchboard_superior_circuit_breaker_manufacturer=get_value("switchboard_superior_circuit_breaker_manufacturer"),
        switchboard_superior_circuit_breaker_model=get_value("switchboard_superior_circuit_breaker_model"),
        switchboard_main_switch=get_value("switchboard_main_switch"),
        switchboard_note=get_value("switchboard_note"),
        switchboard_cable=get_value("switchboard_cable"),
        switchboard_cable_installation_method=get_value("switchboard_cable_installation_method")
    )
    
    db.add(new_switchboard)
    db.commit()
    db.refresh(new_switchboard)
    
    # Redirect to switchboard detail
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/switchboard/{new_switchboard.switchboard_id}", status_code=303)


# Quick Add - Get list with form (for HTMX)
@app.get("/revision/{revision_id}/switchboard/list-with-form", response_class=HTMLResponse)
async def switchboard_list_with_form(revision_id: int, request: Request, db: Session = Depends(get_db)):
    """
    Returns the list of switchboards + empty form container for HTMX
    """
    user_id = get_current_user(request)
    revision = db.query(Revision).filter(
        Revision.revision_id == revision_id,
        Revision.user_id == user_id
    ).first()
    
    if not revision:
        return "<div class='text-red-500 p-4'>Revize nenalezena</div>"
    
    # Get dropdown sources for form
    dropdown_sources = {}
    categories = db.query(DropdownSource.category).distinct().all()
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    return templates.TemplateResponse("components/switchboard_list_with_form.html", {
        "request": request,
        "revision_id": revision_id,
        "switchboards": revision.switchboards,
        "dropdown_sources": dropdown_sources,
        "show_form": False
    })


# Quick Add - Get form (for HTMX)
@app.get("/revision/{revision_id}/switchboard/quick-add-form", response_class=HTMLResponse)
async def get_switchboard_quick_add_form(
    revision_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Returns HTML with inline form for adding switchboard
    """
    user_id = get_current_user(request)
    
    # Verify revision ownership
    revision = db.query(Revision).filter(
        Revision.revision_id == revision_id,
        Revision.user_id == user_id
    ).first()
    
    if not revision:
        return "<div class='text-red-500 p-4'>Revize nenalezena</div>"
    
    # Get dropdown sources for form
    dropdown_sources = {}
    categories = db.query(DropdownSource.category).distinct().all()
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    return templates.TemplateResponse("components/quick_add_switchboard_form.html", {
        "request": request,
        "revision_id": revision_id,
        "dropdown_sources": dropdown_sources
    })


# Quick Add - Submit and refresh (for HTMX)
@app.post("/revision/{revision_id}/switchboard/quick-add", response_class=HTMLResponse)
async def quick_add_switchboard(
    revision_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Creates new switchboard and returns updated list + empty form
    """
    user_id = get_current_user(request)
    
    # Verify revision ownership
    revision = db.query(Revision).filter(
        Revision.revision_id == revision_id,
        Revision.user_id == user_id
    ).first()
    
    if not revision:
        return "<div class='text-red-500 p-4'>Revize nenalezena</div>"
    
    form_data = await request.form()
    
    # Helper function
    def get_value(key, convert_type=None):
        value = form_data.get(key, "").strip()
        if not value:
            return None
        if convert_type == int:
            return int(value) if value else None
        if convert_type == float:
            return float(value) if value else None
        return value
    
    # Auto-determine order if not provided
    order = get_value("switchboard_order", int)
    if order is None:
        max_order = db.query(func.max(Switchboard.switchboard_order)).filter(
            Switchboard.revision_id == revision_id
        ).scalar()
        order = (max_order or 0) + 1
    
    # Create new switchboard
    new_switchboard = Switchboard(
        revision_id=revision_id,
        switchboard_name=get_value("switchboard_name"),
        switchboard_description=get_value("switchboard_description"),
        switchboard_location=get_value("switchboard_location"),
        switchboard_order=order,
        switchboard_type=get_value("switchboard_type"),
        switchboard_serial_number=get_value("switchboard_serial_number"),
        switchboard_production_date=get_value("switchboard_production_date"),
        switchboard_ip_rating=get_value("switchboard_ip_rating"),
        switchboard_impact_protection=get_value("switchboard_impact_protection"),
        switchboard_protection_class=get_value("switchboard_protection_class"),
        switchboard_rated_current=get_value("switchboard_rated_current", float),
        switchboard_rated_voltage=get_value("switchboard_rated_voltage", float),
        switchboard_manufacturer=get_value("switchboard_manufacturer"),
        switchboard_manufacturer_address=get_value("switchboard_manufacturer_address"),
        switchboard_standards=get_value("switchboard_standards"),
        switchboard_enclosure_type=get_value("switchboard_enclosure_type"),
        switchboard_enclosure_manufacturer=get_value("switchboard_enclosure_manufacturer"),
        switchboard_enclosure_installation_method=get_value("switchboard_enclosure_installation_method"),
        switchboard_superior_switchboard=get_value("switchboard_superior_switchboard"),
        switchboard_superior_circuit_breaker_rated_current=get_value("switchboard_superior_circuit_breaker_rated_current", float),
        switchboard_superior_circuit_breaker_trip_characteristic=get_value("switchboard_superior_circuit_breaker_trip_characteristic"),
        switchboard_superior_circuit_breaker_manufacturer=get_value("switchboard_superior_circuit_breaker_manufacturer"),
        switchboard_superior_circuit_breaker_model=get_value("switchboard_superior_circuit_breaker_model"),
        switchboard_main_switch=get_value("switchboard_main_switch"),
        switchboard_note=get_value("switchboard_note"),
        switchboard_cable=get_value("switchboard_cable"),
        switchboard_cable_installation_method=get_value("switchboard_cable_installation_method")
    )
    
    db.add(new_switchboard)
    db.commit()
    db.refresh(new_switchboard)
    
    # Return updated list + empty form
    revision = db.query(Revision).filter(Revision.revision_id == revision_id).first()
    
    # Get dropdown sources for form
    dropdown_sources = {}
    categories = db.query(DropdownSource.category).distinct().all()
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    return templates.TemplateResponse("components/switchboard_list_with_form.html", {
        "request": request,
        "revision_id": revision_id,
        "switchboards": revision.switchboards,
        "dropdown_sources": dropdown_sources,
        "show_form": False  # Hide form after successful submit
    })


# === DEVICE QUICK ADD ENDPOINTS ===

@app.get("/switchboard/{switchboard_id}/device/list-with-form", response_class=HTMLResponse)
async def device_list_with_form(switchboard_id: int, request: Request, db: Session = Depends(get_db)):
    """
    Returns the list of devices + empty form container for HTMX
    """
    user_id = get_current_user(request)
    switchboard = db.query(Switchboard).join(Revision).filter(
        Switchboard.switchboard_id == switchboard_id,
        Revision.user_id == user_id
    ).first()
    
    if not switchboard:
        return "<div class='text-red-500 p-4'>Rozváděč nenalezen</div>"
    
    # Get dropdown sources for form
    dropdown_sources = {}
    categories = db.query(DropdownSource.category).distinct().all()
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    return templates.TemplateResponse("components/device_list_with_form.html", {
        "request": request,
        "switchboard_id": switchboard_id,
        "devices": switchboard.devices,
        "dropdown_sources": dropdown_sources,
        "show_form": False
    })


@app.get("/switchboard/{switchboard_id}/device/quick-add-form", response_class=HTMLResponse)
async def get_device_quick_add_form(
    switchboard_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Returns HTML with inline form for adding device
    """
    user_id = get_current_user(request)
    
    # Verify switchboard ownership
    switchboard = db.query(Switchboard).join(Revision).filter(
        Switchboard.switchboard_id == switchboard_id,
        Revision.user_id == user_id
    ).first()
    
    if not switchboard:
        return "<div class='text-red-500 p-4'>Rozváděč nenalezen</div>"
    
    # Get dropdown sources for form
    dropdown_sources = {}
    categories = db.query(DropdownSource.category).distinct().all()
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    return templates.TemplateResponse("components/quick_add_device_form.html", {
        "request": request,
        "switchboard_id": switchboard_id,
        "dropdown_sources": dropdown_sources
    })


@app.post("/switchboard/{switchboard_id}/device/quick-add", response_class=HTMLResponse)
async def quick_add_device(
    switchboard_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Creates new device and returns updated list + empty form
    """
    user_id = get_current_user(request)
    
    # Verify switchboard ownership
    switchboard = db.query(Switchboard).join(Revision).filter(
        Switchboard.switchboard_id == switchboard_id,
        Revision.user_id == user_id
    ).first()
    
    if not switchboard:
        return "<div class='text-red-500 p-4'>Rozváděč nenalezen</div>"
    
    form_data = await request.form()
    
    # Helper function
    def get_value(key, convert_type=None):
        value = form_data.get(key, "").strip()
        if not value:
            return None
        if convert_type == int:
            return int(value) if value else None
        if convert_type == float:
            return float(value) if value else None
        return value
    
    # Create new device using SwitchboardDevice model
    new_device = SwitchboardDevice(
        switchboard_id=switchboard_id,
        switchboard_device_position=get_value("switchboard_device_position"),
        switchboard_device_type=get_value("switchboard_device_type"),
        switchboard_device_manufacturer=get_value("switchboard_device_manufacturer"),
        switchboard_device_model=get_value("switchboard_device_model"),
        switchboard_device_trip_characteristic=get_value("switchboard_device_trip_characteristic"),
        switchboard_device_rated_current=get_value("switchboard_device_rated_current", float),
        switchboard_device_residual_current_ma=get_value("switchboard_device_residual_current_ma", float),
        switchboard_device_poles=get_value("switchboard_device_poles", int),
        switchboard_device_module_width=get_value("switchboard_device_module_width", float)
    )
    
    db.add(new_device)
    db.commit()
    db.refresh(new_device)
    
    # Return updated list + empty form
    switchboard = db.query(Switchboard).filter(Switchboard.switchboard_id == switchboard_id).first()
    
    # Get dropdown sources for form
    dropdown_sources = {}
    categories = db.query(DropdownSource.category).distinct().all()
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    return templates.TemplateResponse("components/device_list_with_form.html", {
        "request": request,
        "switchboard_id": switchboard_id,
        "devices": switchboard.devices,
        "dropdown_sources": dropdown_sources,
        "show_form": False  # Hide form after successful submit
    })


# Read - Show detail (NEW CARD-BASED VERSION)
@app.get("/switchboard/{switchboard_id}", response_class=HTMLResponse)
async def switchboard_detail(switchboard_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    switchboard = db.query(Switchboard).join(Revision).filter(
        Switchboard.switchboard_id == switchboard_id,
        Revision.user_id == user_id
    ).first()
    
    if not switchboard:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    return templates.TemplateResponse("switchboard_detail_redesigned.html", {
        "request": request,
        "user_id": user_id,
        "switchboard": switchboard,
        "sidebar_revisions": get_sidebar_revisions(db, user_id),
        "current_revision_for_sidebar": switchboard.revision
    })


# PHASE 5: Card-based detail views - Get static card view for switchboard
@app.get("/switchboard/{switchboard_id}/card/{card_type}", response_class=HTMLResponse)
async def get_switchboard_card(switchboard_id: int, card_type: str, request: Request, db: Session = Depends(get_db)):
    """Return static view of a specific card"""
    user_id = get_current_user(request)
    switchboard = db.query(Switchboard).join(Revision).filter(
        Switchboard.switchboard_id == switchboard_id,
        Revision.user_id == user_id
    ).first()
    
    if not switchboard:
        return HTMLResponse(content="<div class='p-4 text-red-500'>Rozváděč nenalezen</div>", status_code=404)
    
    template_name = f"cards/switchboard_static_{card_type}.html"
    return templates.TemplateResponse(template_name, {
        "request": request,
        "switchboard": switchboard
    })


# PHASE 5: Get edit form for switchboard card
@app.get("/switchboard/{switchboard_id}/edit-card/{card_type}", response_class=HTMLResponse)
async def get_switchboard_card_edit(switchboard_id: int, card_type: str, request: Request, db: Session = Depends(get_db)):
    """Return edit form for a specific card"""
    user_id = get_current_user(request)
    switchboard = db.query(Switchboard).join(Revision).filter(
        Switchboard.switchboard_id == switchboard_id,
        Revision.user_id == user_id
    ).first()
    
    if not switchboard:
        return HTMLResponse(content="<div class='p-4 text-red-500'>Rozváděč nenalezen</div>", status_code=404)
    
    # 🔧 BUGFIX: Add field configs and dropdown sources for dynamic rendering
    field_configs = get_entity_field_config('switchboard', db)
    
    # Get all dropdown sources grouped by category
    categories = db.query(DropdownSource.category).distinct().all()
    dropdown_sources = {}
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    template_name = f"cards/switchboard_edit_{card_type}.html"
    return templates.TemplateResponse(template_name, {
        "request": request,
        "switchboard": switchboard,
        "field_configs": field_configs,
        "dropdown_sources": dropdown_sources
    })


# PHASE 5: Update switchboard card data
@app.post("/switchboard/{switchboard_id}/update-card/{card_type}", response_class=HTMLResponse)
async def update_switchboard_card(switchboard_id: int, card_type: str, request: Request, db: Session = Depends(get_db)):
    """Update card data and return static view"""
    user_id = get_current_user(request)
    switchboard = db.query(Switchboard).join(Revision).filter(
        Switchboard.switchboard_id == switchboard_id,
        Revision.user_id == user_id
    ).first()
    
    if not switchboard:
        return HTMLResponse(content="<div class='p-4 text-red-500'>Rozváděč nenalezen</div>", status_code=404)
    
    form_data = await request.form()
    
    # Helper function to convert empty strings to None
    def get_value(key, convert_type=None):
        value = form_data.get(key, "").strip()
        if not value:
            return None
        if convert_type == int:
            return int(value) if value else None
        if convert_type == float:
            return float(value) if value else None
        return value
    
    # Update fields based on card type
    if card_type == 'basic':
        switchboard.switchboard_name = get_value("switchboard_name")
        switchboard.switchboard_location = get_value("switchboard_location")
        switchboard.switchboard_order = get_value("switchboard_order", int)
        switchboard.switchboard_type = get_value("switchboard_type")
        switchboard.switchboard_description = get_value("switchboard_description")
    
    elif card_type == 'technical':
        switchboard.protection_class = get_value("protection_class")
        switchboard.ip_rating = get_value("ip_rating")
        switchboard.ik_rating = get_value("ik_rating")
        switchboard.environment = get_value("environment")
        switchboard.protective_device = get_value("protective_device")
    
    db.commit()
    
    # Return static view
    template_name = f"cards/switchboard_static_{card_type}.html"
    return templates.TemplateResponse(template_name, {
        "request": request,
        "switchboard": switchboard
    })


# Update - Show edit form
@app.get("/switchboard/{switchboard_id}/edit", response_class=HTMLResponse)
async def switchboard_edit_form(switchboard_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    switchboard = db.query(Switchboard).join(Revision).filter(
        Switchboard.switchboard_id == switchboard_id,
        Revision.user_id == user_id
    ).first()
    
    if not switchboard:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    # Get dropdown configuration for switchboard
    dropdown_config = get_field_dropdown_config("switchboard", db)
    
    # PHASE 4: Get field configuration
    field_configs = get_entity_field_config('switchboard', db)
    
    # Get all dropdown sources grouped by category
    categories = db.query(DropdownSource.category).distinct().all()
    dropdown_sources = {}
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    return templates.TemplateResponse("switchboard_form.html", {
        "request": request,
        "user_id": user_id,
        "revision": switchboard.revision,
        "switchboard": switchboard,
        "dropdown_config": dropdown_config,
        "dropdown_sources": dropdown_sources,
        "field_configs": field_configs
    })


# Update - Save changes
@app.post("/switchboard/{switchboard_id}/update")
async def switchboard_update(switchboard_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    switchboard = db.query(Switchboard).join(Revision).filter(
        Switchboard.switchboard_id == switchboard_id,
        Revision.user_id == user_id
    ).first()
    
    if not switchboard:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    form_data = await request.form()
    
    # Helper function
    def get_value(key, convert_type=None):
        value = form_data.get(key, "").strip()
        if not value:
            return None
        if convert_type == int:
            return int(value) if value else None
        if convert_type == float:
            return float(value) if value else None
        return value
    
    # Update switchboard fields
    switchboard.switchboard_name = get_value("switchboard_name")
    switchboard.switchboard_description = get_value("switchboard_description")
    switchboard.switchboard_location = get_value("switchboard_location")
    switchboard.switchboard_order = get_value("switchboard_order", int)
    switchboard.switchboard_type = get_value("switchboard_type")
    switchboard.switchboard_serial_number = get_value("switchboard_serial_number")
    switchboard.switchboard_production_date = get_value("switchboard_production_date")
    switchboard.switchboard_ip_rating = get_value("switchboard_ip_rating")
    switchboard.switchboard_impact_protection = get_value("switchboard_impact_protection")
    switchboard.switchboard_protection_class = get_value("switchboard_protection_class")
    switchboard.switchboard_rated_current = get_value("switchboard_rated_current", float)
    switchboard.switchboard_rated_voltage = get_value("switchboard_rated_voltage", float)
    switchboard.switchboard_manufacturer = get_value("switchboard_manufacturer")
    switchboard.switchboard_manufacturer_address = get_value("switchboard_manufacturer_address")
    switchboard.switchboard_standards = get_value("switchboard_standards")
    switchboard.switchboard_enclosure_type = get_value("switchboard_enclosure_type")
    switchboard.switchboard_enclosure_manufacturer = get_value("switchboard_enclosure_manufacturer")
    switchboard.switchboard_enclosure_installation_method = get_value("switchboard_enclosure_installation_method")
    switchboard.switchboard_superior_switchboard = get_value("switchboard_superior_switchboard")
    switchboard.switchboard_superior_circuit_breaker_rated_current = get_value("switchboard_superior_circuit_breaker_rated_current", float)
    switchboard.switchboard_superior_circuit_breaker_trip_characteristic = get_value("switchboard_superior_circuit_breaker_trip_characteristic")
    switchboard.switchboard_superior_circuit_breaker_manufacturer = get_value("switchboard_superior_circuit_breaker_manufacturer")
    switchboard.switchboard_superior_circuit_breaker_model = get_value("switchboard_superior_circuit_breaker_model")
    switchboard.switchboard_main_switch = get_value("switchboard_main_switch")
    switchboard.switchboard_note = get_value("switchboard_note")
    switchboard.switchboard_cable = get_value("switchboard_cable")
    switchboard.switchboard_cable_installation_method = get_value("switchboard_cable_installation_method")
    
    db.commit()
    
    # Redirect to switchboard detail
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/switchboard/{switchboard_id}", status_code=303)


# Delete
@app.post("/switchboard/{switchboard_id}/delete")
async def switchboard_delete(switchboard_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    switchboard = db.query(Switchboard).join(Revision).filter(
        Switchboard.switchboard_id == switchboard_id,
        Revision.user_id == user_id
    ).first()
    
    if switchboard:
        revision_id = switchboard.revision_id
        db.delete(switchboard)
        db.commit()
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"/revision/{revision_id}", status_code=303)
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=303)


# Duplicate
@app.post("/switchboard/{switchboard_id}/duplicate")
async def switchboard_duplicate(switchboard_id: int, request: Request, db: Session = Depends(get_db)):
    from fastapi.responses import RedirectResponse
    
    user_id = get_current_user(request)
    original = db.query(Switchboard).join(Revision).filter(
        Switchboard.switchboard_id == switchboard_id,
        Revision.user_id == user_id
    ).first()
    
    if not original:
        return RedirectResponse(url="/", status_code=303)
    
    # Create new switchboard
    new_switchboard = Switchboard(
        revision_id=original.revision_id,
        switchboard_name=f"{original.switchboard_name or ''} (kopie)" if original.switchboard_name else "Kopie",
        switchboard_description=original.switchboard_description,
        switchboard_location=original.switchboard_location,
        switchboard_order=original.switchboard_order,
        switchboard_type=original.switchboard_type,
        switchboard_serial_number=original.switchboard_serial_number,
        switchboard_production_date=original.switchboard_production_date,
        switchboard_ip_rating=original.switchboard_ip_rating,
        switchboard_impact_protection=original.switchboard_impact_protection,
        switchboard_protection_class=original.switchboard_protection_class,
        switchboard_rated_current=original.switchboard_rated_current,
        switchboard_rated_voltage=original.switchboard_rated_voltage,
        switchboard_manufacturer=original.switchboard_manufacturer,
        switchboard_manufacturer_address=original.switchboard_manufacturer_address,
        switchboard_standards=original.switchboard_standards,
        switchboard_enclosure_type=original.switchboard_enclosure_type,
        switchboard_enclosure_manufacturer=original.switchboard_enclosure_manufacturer,
        switchboard_enclosure_installation_method=original.switchboard_enclosure_installation_method,
        switchboard_superior_switchboard=original.switchboard_superior_switchboard,
        switchboard_superior_circuit_breaker_rated_current=original.switchboard_superior_circuit_breaker_rated_current,
        switchboard_superior_circuit_breaker_trip_characteristic=original.switchboard_superior_circuit_breaker_trip_characteristic,
        switchboard_superior_circuit_breaker_manufacturer=original.switchboard_superior_circuit_breaker_manufacturer,
        switchboard_superior_circuit_breaker_model=original.switchboard_superior_circuit_breaker_model,
        switchboard_main_switch=original.switchboard_main_switch,
        switchboard_note=original.switchboard_note,
        switchboard_cable=original.switchboard_cable,
        switchboard_cable_installation_method=original.switchboard_cable_installation_method
    )
    db.add(new_switchboard)
    db.flush()
    
    # Duplicate measurements
    if original.measurements:
        new_measurement = SwitchboardMeasurement(
            switchboard_id=new_switchboard.switchboard_id,
            measurements_switchboard_insulation_resistance=original.measurements.measurements_switchboard_insulation_resistance,
            measurements_switchboard_loop_impedance_min=original.measurements.measurements_switchboard_loop_impedance_min,
            measurements_switchboard_loop_impedance_max=original.measurements.measurements_switchboard_loop_impedance_max,
            measurements_switchboard_rcd_trip_time_ms=original.measurements.measurements_switchboard_rcd_trip_time_ms,
            measurements_switchboard_rcd_test_current_ma=original.measurements.measurements_switchboard_rcd_test_current_ma,
            measurements_switchboard_earth_resistance=original.measurements.measurements_switchboard_earth_resistance
        )
        db.add(new_measurement)
    
    # Duplicate devices
    device_id_map = {}
    devices_to_process = [d for d in original.devices if d.parent_device_id is None]
    
    while devices_to_process:
        device = devices_to_process.pop(0)
        new_device = SwitchboardDevice(
            switchboard_id=new_switchboard.switchboard_id,
            parent_device_id=device_id_map.get(device.parent_device_id),
            switchboard_device_position=device.switchboard_device_position,
            switchboard_device_type=device.switchboard_device_type,
            switchboard_device_manufacturer=device.switchboard_device_manufacturer,
            switchboard_device_model=device.switchboard_device_model,
            switchboard_device_trip_characteristic=device.switchboard_device_trip_characteristic,
            switchboard_device_rated_current=device.switchboard_device_rated_current,
            switchboard_device_residual_current_ma=device.switchboard_device_residual_current_ma,
            switchboard_device_sub_devices=device.switchboard_device_sub_devices,
            switchboard_device_poles=device.switchboard_device_poles,
            switchboard_device_module_width=device.switchboard_device_module_width
        )
        db.add(new_device)
        db.flush()
        device_id_map[device.device_id] = new_device.device_id
        
        # Duplicate circuits
        for circuit in device.circuits:
            new_circuit = Circuit(
                device_id=new_device.device_id,
                circuit_number=circuit.circuit_number,
                circuit_room=circuit.circuit_room,
                circuit_description=circuit.circuit_description,
                circuit_description_from_switchboard=circuit.circuit_description_from_switchboard,
                circuit_number_of_outlets=circuit.circuit_number_of_outlets,
                circuit_cable_termination=circuit.circuit_cable_termination,
                circuit_cable=circuit.circuit_cable,
                circuit_cable_installation_method=circuit.circuit_cable_installation_method
            )
            db.add(new_circuit)
            db.flush()
            
            # Duplicate circuit measurements
            if circuit.measurements:
                new_circuit_measurement = CircuitMeasurement(
                    circuit_id=new_circuit.circuit_id,
                    measurements_circuit_insulation_resistance=circuit.measurements.measurements_circuit_insulation_resistance,
                    measurements_circuit_loop_impedance_min=circuit.measurements.measurements_circuit_loop_impedance_min,
                    measurements_circuit_loop_impedance_max=circuit.measurements.measurements_circuit_loop_impedance_max,
                    measurements_circuit_rcd_trip_time_ms=circuit.measurements.measurements_circuit_rcd_trip_time_ms,
                    measurements_circuit_rcd_test_current_ma=circuit.measurements.measurements_circuit_rcd_test_current_ma,
                    measurements_circuit_earth_resistance=circuit.measurements.measurements_circuit_earth_resistance,
                    measurements_circuit_continuity=circuit.measurements.measurements_circuit_continuity,
                    measurements_circuit_order_of_phases=circuit.measurements.measurements_circuit_order_of_phases
                )
                db.add(new_circuit_measurement)
            
            # Duplicate terminal devices
            for terminal in circuit.terminal_devices:
                new_terminal = TerminalDevice(
                    circuit_id=new_circuit.circuit_id,
                    terminal_device_type=terminal.terminal_device_type,
                    terminal_device_manufacturer=terminal.terminal_device_manufacturer,
                    terminal_device_model=terminal.terminal_device_model,
                    terminal_device_marking=terminal.terminal_device_marking,
                    terminal_device_power=terminal.terminal_device_power,
                    terminal_device_ip_rating=terminal.terminal_device_ip_rating,
                    terminal_device_protection_class=terminal.terminal_device_protection_class,
                    terminal_device_serial_number=terminal.terminal_device_serial_number,
                    terminal_device_supply_type=terminal.terminal_device_supply_type,
                    terminal_device_installation_method=terminal.terminal_device_installation_method
                )
                db.add(new_terminal)
        
        # Add child devices to process
        for child in device.child_devices:
            devices_to_process.append(child)
    
    db.commit()
    return RedirectResponse(url=f"/switchboard/{new_switchboard.switchboard_id}", status_code=303)


# SWITCHBOARD MEASUREMENT CRUD ENDPOINTS

# Create - Show form
@app.get("/switchboard/{switchboard_id}/measurement/create", response_class=HTMLResponse)
async def measurement_create_form(switchboard_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    switchboard = db.query(Switchboard).join(Revision).filter(
        Switchboard.switchboard_id == switchboard_id,
        Revision.user_id == user_id
    ).first()
    
    if not switchboard:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    # Check if measurement already exists (1:1 relationship)
    if switchboard.measurements:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"/switchboard/{switchboard_id}/measurement/edit", status_code=303)
    
    return templates.TemplateResponse("measurement_form.html", {
        "request": request,
        "user_id": user_id,
        "switchboard": switchboard,
        "measurement": None
    })


# Create - Save new measurement
@app.post("/switchboard/{switchboard_id}/measurement/create")
async def measurement_create(switchboard_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    switchboard = db.query(Switchboard).join(Revision).filter(
        Switchboard.switchboard_id == switchboard_id,
        Revision.user_id == user_id
    ).first()
    
    if not switchboard:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    # Check if measurement already exists
    if switchboard.measurements:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"/switchboard/{switchboard_id}", status_code=303)
    
    form_data = await request.form()
    
    # Helper function
    def get_value(key, convert_type=None):
        value = form_data.get(key, "").strip()
        if not value:
            return None
        if convert_type == float:
            return float(value) if value else None
        return value
    
    # Create new measurement
    new_measurement = SwitchboardMeasurement(
        switchboard_id=switchboard_id,
        measurements_switchboard_insulation_resistance=get_value("measurements_switchboard_insulation_resistance", float),
        measurements_switchboard_loop_impedance_min=get_value("measurements_switchboard_loop_impedance_min", float),
        measurements_switchboard_loop_impedance_max=get_value("measurements_switchboard_loop_impedance_max", float),
        measurements_switchboard_rcd_trip_time_ms=get_value("measurements_switchboard_rcd_trip_time_ms", float),
        measurements_switchboard_rcd_test_current_ma=get_value("measurements_switchboard_rcd_test_current_ma", float),
        measurements_switchboard_earth_resistance=get_value("measurements_switchboard_earth_resistance", float)
    )
    
    db.add(new_measurement)
    db.commit()
    
    # Redirect to switchboard detail
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/switchboard/{switchboard_id}", status_code=303)


# Update - Show edit form
@app.get("/switchboard/{switchboard_id}/measurement/edit", response_class=HTMLResponse)
async def measurement_edit_form(switchboard_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    switchboard = db.query(Switchboard).join(Revision).filter(
        Switchboard.switchboard_id == switchboard_id,
        Revision.user_id == user_id
    ).first()
    
    if not switchboard or not switchboard.measurements:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"/switchboard/{switchboard_id}", status_code=303)
    
    return templates.TemplateResponse("measurement_form.html", {
        "request": request,
        "user_id": user_id,
        "switchboard": switchboard,
        "measurement": switchboard.measurements
    })


# Update - Save changes
@app.post("/measurement/{measurement_id}/update")
async def measurement_update(measurement_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    measurement = db.query(SwitchboardMeasurement).join(Switchboard).join(Revision).filter(
        SwitchboardMeasurement.measurement_id == measurement_id,
        Revision.user_id == user_id
    ).first()
    
    if not measurement:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    form_data = await request.form()
    
    # Helper function
    def get_value(key, convert_type=None):
        value = form_data.get(key, "").strip()
        if not value:
            return None
        if convert_type == float:
            return float(value) if value else None
        return value
    
    # Update measurement fields
    measurement.measurements_switchboard_insulation_resistance = get_value("measurements_switchboard_insulation_resistance", float)
    measurement.measurements_switchboard_loop_impedance_min = get_value("measurements_switchboard_loop_impedance_min", float)
    measurement.measurements_switchboard_loop_impedance_max = get_value("measurements_switchboard_loop_impedance_max", float)
    measurement.measurements_switchboard_rcd_trip_time_ms = get_value("measurements_switchboard_rcd_trip_time_ms", float)
    measurement.measurements_switchboard_rcd_test_current_ma = get_value("measurements_switchboard_rcd_test_current_ma", float)
    measurement.measurements_switchboard_earth_resistance = get_value("measurements_switchboard_earth_resistance", float)
    
    db.commit()
    
    # Redirect to switchboard detail
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/switchboard/{measurement.switchboard_id}", status_code=303)


# Delete
@app.post("/measurement/{measurement_id}/delete")
async def measurement_delete(measurement_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    measurement = db.query(SwitchboardMeasurement).join(Switchboard).join(Revision).filter(
        SwitchboardMeasurement.measurement_id == measurement_id,
        Revision.user_id == user_id
    ).first()
    
    if measurement:
        switchboard_id = measurement.switchboard_id
        db.delete(measurement)
        db.commit()
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"/switchboard/{switchboard_id}", status_code=303)
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=303)


# ===== SWITCHBOARD DEVICE (PŘÍSTROJE V ROZVÁDĚČI) =====

# Create - Show form
@app.get("/switchboard/{switchboard_id}/device/create", response_class=HTMLResponse)
async def device_create_form(switchboard_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Verify ownership through switchboard -> revision
    switchboard = db.query(Switchboard).join(Revision).filter(
        Switchboard.switchboard_id == switchboard_id,
        Revision.user_id == user_id
    ).first()
    
    if not switchboard:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    # Get all devices in this switchboard for parent selection
    devices = db.query(SwitchboardDevice).filter(
        SwitchboardDevice.switchboard_id == switchboard_id
    ).order_by(SwitchboardDevice.switchboard_device_position).all()
    
    # Get dropdown configuration for device
    dropdown_config = get_field_dropdown_config("device", db)
    
    # PHASE 4: Get field configuration
    field_configs = get_entity_field_config('device', db)
    
    # Get all dropdown sources grouped by category
    categories = db.query(DropdownSource.category).distinct().all()
    dropdown_sources = {}
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    return templates.TemplateResponse("device_form.html", {
        "request": request,
        "user_id": user_id,
        "switchboard": switchboard,
        "device": None,
        "devices": devices,
        "dropdown_config": dropdown_config,
        "dropdown_sources": dropdown_sources,
        "field_configs": field_configs
    })


# Create - Save new device
@app.post("/switchboard/{switchboard_id}/device/create")
async def device_create(switchboard_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    form_data = await request.form()
    
    # Verify ownership
    switchboard = db.query(Switchboard).join(Revision).filter(
        Switchboard.switchboard_id == switchboard_id,
        Revision.user_id == user_id
    ).first()
    
    if not switchboard:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    def get_value(key, convert_type=None):
        value = form_data.get(key, "").strip()
        if not value:
            return None
        if convert_type == int:
            return int(value) if value else None
        if convert_type == float:
            return float(value) if value else None
        return value
    
    # Create new device
    new_device = SwitchboardDevice(
        switchboard_id=switchboard_id,
        parent_device_id=get_value("parent_device_id", int),
        switchboard_device_position=get_value("switchboard_device_position"),
        switchboard_device_type=get_value("switchboard_device_type"),
        switchboard_device_manufacturer=get_value("switchboard_device_manufacturer"),
        switchboard_device_model=get_value("switchboard_device_model"),
        switchboard_device_trip_characteristic=get_value("switchboard_device_trip_characteristic"),
        switchboard_device_rated_current=get_value("switchboard_device_rated_current", float),
        switchboard_device_residual_current_ma=get_value("switchboard_device_residual_current_ma", float),
        switchboard_device_sub_devices=get_value("switchboard_device_sub_devices"),
        switchboard_device_poles=get_value("switchboard_device_poles", int),
        switchboard_device_module_width=get_value("switchboard_device_module_width", float)
    )
    
    db.add(new_device)
    db.commit()
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/switchboard/{switchboard_id}", status_code=303)


# Update - Show form
@app.get("/device/{device_id}/edit", response_class=HTMLResponse)
async def device_edit_form(device_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Verify ownership through device -> switchboard -> revision
    device = db.query(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        SwitchboardDevice.device_id == device_id,
        Revision.user_id == user_id
    ).first()
    
    if not device:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    # Get all devices in this switchboard for parent selection (exclude self and descendants)
    devices = db.query(SwitchboardDevice).filter(
        SwitchboardDevice.switchboard_id == device.switchboard_id,
        SwitchboardDevice.device_id != device_id
    ).order_by(SwitchboardDevice.switchboard_device_position).all()
    
    # Get dropdown configuration for device
    dropdown_config = get_field_dropdown_config("device", db)
    
    # PHASE 4: Get field configuration
    field_configs = get_entity_field_config('device', db)
    
    # Get all dropdown sources grouped by category
    categories = db.query(DropdownSource.category).distinct().all()
    dropdown_sources = {}
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    return templates.TemplateResponse("device_form.html", {
        "request": request,
        "user_id": user_id,
        "switchboard": device.switchboard,
        "device": device,
        "devices": devices,
        "dropdown_config": dropdown_config,
        "dropdown_sources": dropdown_sources,
        "field_configs": field_configs
    })


# Update - Save
@app.post("/device/{device_id}/update")
async def device_update(device_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    form_data = await request.form()
    
    # Verify ownership
    device = db.query(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        SwitchboardDevice.device_id == device_id,
        Revision.user_id == user_id
    ).first()
    
    if not device:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    def get_value(key, convert_type=None):
        value = form_data.get(key, "").strip()
        if not value:
            return None
        if convert_type == int:
            return int(value) if value else None
        if convert_type == float:
            return float(value) if value else None
        return value
    
    # Update device fields
    device.parent_device_id = get_value("parent_device_id", int)
    device.switchboard_device_position = get_value("switchboard_device_position")
    device.switchboard_device_type = get_value("switchboard_device_type")
    device.switchboard_device_manufacturer = get_value("switchboard_device_manufacturer")
    device.switchboard_device_model = get_value("switchboard_device_model")
    device.switchboard_device_trip_characteristic = get_value("switchboard_device_trip_characteristic")
    device.switchboard_device_rated_current = get_value("switchboard_device_rated_current", float)
    device.switchboard_device_residual_current_ma = get_value("switchboard_device_residual_current_ma", float)
    device.switchboard_device_sub_devices = get_value("switchboard_device_sub_devices")
    device.switchboard_device_poles = get_value("switchboard_device_poles", int)
    device.switchboard_device_module_width = get_value("switchboard_device_module_width", float)
    
    db.commit()
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/switchboard/{device.switchboard_id}", status_code=303)


# Delete
@app.post("/device/{device_id}/delete")
async def device_delete(device_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Verify ownership
    device = db.query(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        SwitchboardDevice.device_id == device_id,
        Revision.user_id == user_id
    ).first()
    
    if device:
        switchboard_id = device.switchboard_id
        # SQLAlchemy will handle cascade delete of child devices due to self-referencing relationship
        db.delete(device)
        db.commit()
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"/switchboard/{switchboard_id}", status_code=303)
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=303)


# Duplicate
@app.post("/device/{device_id}/duplicate")
async def device_duplicate(device_id: int, request: Request, db: Session = Depends(get_db)):
    from fastapi.responses import RedirectResponse
    
    user_id = get_current_user(request)
    original = db.query(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        SwitchboardDevice.device_id == device_id,
        Revision.user_id == user_id
    ).first()
    
    if not original:
        return RedirectResponse(url="/", status_code=303)
    
    # Recursive function to duplicate device and its children
    def duplicate_device_recursive(source_device, new_switchboard_id, new_parent_id=None):
        new_device = SwitchboardDevice(
            switchboard_id=new_switchboard_id,
            parent_device_id=new_parent_id,
            switchboard_device_position=f"{source_device.switchboard_device_position or ''} (kopie)" if source_device.switchboard_device_position else "Kopie",
            switchboard_device_type=source_device.switchboard_device_type,
            switchboard_device_manufacturer=source_device.switchboard_device_manufacturer,
            switchboard_device_model=source_device.switchboard_device_model,
            switchboard_device_trip_characteristic=source_device.switchboard_device_trip_characteristic,
            switchboard_device_rated_current=source_device.switchboard_device_rated_current,
            switchboard_device_residual_current_ma=source_device.switchboard_device_residual_current_ma,
            switchboard_device_sub_devices=source_device.switchboard_device_sub_devices,
            switchboard_device_poles=source_device.switchboard_device_poles,
            switchboard_device_module_width=source_device.switchboard_device_module_width
        )
        db.add(new_device)
        db.flush()
        
        # Duplicate circuits
        for circuit in source_device.circuits:
            new_circuit = Circuit(
                device_id=new_device.device_id,
                circuit_number=circuit.circuit_number,
                circuit_room=circuit.circuit_room,
                circuit_description=circuit.circuit_description,
                circuit_description_from_switchboard=circuit.circuit_description_from_switchboard,
                circuit_number_of_outlets=circuit.circuit_number_of_outlets,
                circuit_cable_termination=circuit.circuit_cable_termination,
                circuit_cable=circuit.circuit_cable,
                circuit_cable_installation_method=circuit.circuit_cable_installation_method
            )
            db.add(new_circuit)
            db.flush()
            
            # Duplicate circuit measurements
            if circuit.measurements:
                new_circuit_measurement = CircuitMeasurement(
                    circuit_id=new_circuit.circuit_id,
                    measurements_circuit_insulation_resistance=circuit.measurements.measurements_circuit_insulation_resistance,
                    measurements_circuit_loop_impedance_min=circuit.measurements.measurements_circuit_loop_impedance_min,
                    measurements_circuit_loop_impedance_max=circuit.measurements.measurements_circuit_loop_impedance_max,
                    measurements_circuit_rcd_trip_time_ms=circuit.measurements.measurements_circuit_rcd_trip_time_ms,
                    measurements_circuit_rcd_test_current_ma=circuit.measurements.measurements_circuit_rcd_test_current_ma,
                    measurements_circuit_earth_resistance=circuit.measurements.measurements_circuit_earth_resistance,
                    measurements_circuit_continuity=circuit.measurements.measurements_circuit_continuity,
                    measurements_circuit_order_of_phases=circuit.measurements.measurements_circuit_order_of_phases
                )
                db.add(new_circuit_measurement)
            
            # Duplicate terminal devices
            for terminal in circuit.terminal_devices:
                new_terminal = TerminalDevice(
                    circuit_id=new_circuit.circuit_id,
                    terminal_device_type=terminal.terminal_device_type,
                    terminal_device_manufacturer=terminal.terminal_device_manufacturer,
                    terminal_device_model=terminal.terminal_device_model,
                    terminal_device_marking=terminal.terminal_device_marking,
                    terminal_device_power=terminal.terminal_device_power,
                    terminal_device_ip_rating=terminal.terminal_device_ip_rating,
                    terminal_device_protection_class=terminal.terminal_device_protection_class,
                    terminal_device_serial_number=terminal.terminal_device_serial_number,
                    terminal_device_supply_type=terminal.terminal_device_supply_type,
                    terminal_device_installation_method=terminal.terminal_device_installation_method
                )
                db.add(new_terminal)
        
        # Duplicate child devices recursively
        for child in source_device.child_devices:
            duplicate_device_recursive(child, new_switchboard_id, new_device.device_id)
        
        return new_device
    
    new_device = duplicate_device_recursive(original, original.switchboard_id, original.parent_device_id)
    db.commit()
    
    return RedirectResponse(url=f"/device/{new_device.device_id}", status_code=303)


# === CIRCUIT QUICK ADD ENDPOINTS ===

@app.get("/device/{device_id}/circuit/list-with-form", response_class=HTMLResponse)
async def circuit_list_with_form(device_id: int, request: Request, db: Session = Depends(get_db)):
    """
    Returns the list of circuits + empty form container for HTMX
    """
    user_id = get_current_user(request)
    device = db.query(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        SwitchboardDevice.device_id == device_id,
        Revision.user_id == user_id
    ).first()
    
    if not device:
        return "<div class='text-red-500 p-4'>Přístroj nenalezen</div>"
    
    # Get dropdown sources for form
    dropdown_sources = {}
    categories = db.query(DropdownSource.category).distinct().all()
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    return templates.TemplateResponse("components/circuit_list_with_form.html", {
        "request": request,
        "device_id": device_id,
        "circuits": device.circuits,
        "dropdown_sources": dropdown_sources,
        "show_form": False
    })


@app.get("/device/{device_id}/circuit/quick-add-form", response_class=HTMLResponse)
async def get_circuit_quick_add_form(
    device_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Returns HTML with inline form for adding circuit
    """
    user_id = get_current_user(request)
    
    # Verify device ownership
    device = db.query(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        SwitchboardDevice.device_id == device_id,
        Revision.user_id == user_id
    ).first()
    
    if not device:
        return "<div class='text-red-500 p-4'>Přístroj nenalezen</div>"
    
    # Get dropdown sources for form
    dropdown_sources = {}
    categories = db.query(DropdownSource.category).distinct().all()
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    return templates.TemplateResponse("components/quick_add_circuit_form.html", {
        "request": request,
        "device_id": device_id,
        "dropdown_sources": dropdown_sources
    })


@app.post("/device/{device_id}/circuit/quick-add", response_class=HTMLResponse)
async def quick_add_circuit(
    device_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Creates new circuit and returns updated list + empty form
    """
    user_id = get_current_user(request)
    
    # Verify device ownership
    device = db.query(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        SwitchboardDevice.device_id == device_id,
        Revision.user_id == user_id
    ).first()
    
    if not device:
        return "<div class='text-red-500 p-4'>Přístroj nenalezen</div>"
    
    form_data = await request.form()
    
    # Helper function
    def get_value(key, convert_type=None):
        value = form_data.get(key, "").strip()
        if not value:
            return None
        if convert_type == int:
            return int(value) if value else None
        if convert_type == float:
            return float(value) if value else None
        return value
    
    # Create new circuit
    new_circuit = Circuit(
        device_id=device_id,
        circuit_number=get_value("circuit_number"),
        circuit_room=get_value("circuit_room"),
        circuit_description=get_value("circuit_description"),
        circuit_description_from_switchboard=get_value("circuit_description_from_switchboard"),
        circuit_number_of_outlets=get_value("circuit_number_of_outlets", int),
        circuit_cable_termination=get_value("circuit_cable_termination"),
        circuit_cable=get_value("circuit_cable"),
        circuit_cable_installation_method=get_value("circuit_cable_installation_method")
    )
    
    db.add(new_circuit)
    db.commit()
    db.refresh(new_circuit)
    
    # Return updated list + empty form
    device = db.query(SwitchboardDevice).filter(SwitchboardDevice.device_id == device_id).first()
    
    # Get dropdown sources for form
    dropdown_sources = {}
    categories = db.query(DropdownSource.category).distinct().all()
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    return templates.TemplateResponse("components/circuit_list_with_form.html", {
        "request": request,
        "device_id": device_id,
        "circuits": device.circuits,
        "dropdown_sources": dropdown_sources,
        "show_form": False  # Hide form after successful submit
    })


# ============================================================================
# CIRCUIT CRUD
# ============================================================================

# CREATE - Show form
@app.get("/device/{device_id}/circuit/create", response_class=HTMLResponse)
async def circuit_create_form(device_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Verify device ownership through switchboard → revision
    device = db.query(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        SwitchboardDevice.device_id == device_id,
        Revision.user_id == user_id
    ).first()
    
    if not device:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    # Get dropdown configuration for circuit
    dropdown_config = get_field_dropdown_config("circuit", db)
    
    # PHASE 4: Get field configuration
    field_configs = get_entity_field_config('circuit', db)
    
    # Get all dropdown sources grouped by category
    categories = db.query(DropdownSource.category).distinct().all()
    dropdown_sources = {}
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    return templates.TemplateResponse("circuit_form.html", {
        "request": request,
        "device": device,
        "circuit": None,
        "is_edit": False,
        "dropdown_config": dropdown_config,
        "dropdown_sources": dropdown_sources,
        "field_configs": field_configs
    })


# CREATE - Process form
@app.post("/device/{device_id}/circuit/create")
async def circuit_create(device_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Verify device ownership
    device = db.query(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        SwitchboardDevice.device_id == device_id,
        Revision.user_id == user_id
    ).first()
    
    if not device:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    form_data = await request.form()
    
    def get_value(key, type_cast=None):
        value = form_data.get(key, "").strip()
        if not value:
            return None
        if type_cast == int:
            try:
                return int(value)
            except ValueError:
                return None
        elif type_cast == float:
            try:
                return float(value)
            except ValueError:
                return None
        return value
    
    # Create circuit
    new_circuit = Circuit(
        device_id=device_id,
        circuit_number=get_value("circuit_number"),
        circuit_room=get_value("circuit_room"),
        circuit_description=get_value("circuit_description"),
        circuit_description_from_switchboard=get_value("circuit_description_from_switchboard"),
        circuit_number_of_outlets=get_value("circuit_number_of_outlets", int),
        circuit_cable_termination=get_value("circuit_cable_termination"),
        circuit_cable=get_value("circuit_cable"),
        circuit_cable_installation_method=get_value("circuit_cable_installation_method")
    )
    
    db.add(new_circuit)
    db.commit()
    db.refresh(new_circuit)
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/circuit/{new_circuit.circuit_id}", status_code=303)


# READ - Circuit detail
@app.get("/circuit/{circuit_id}", response_class=HTMLResponse)
async def circuit_detail(circuit_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Get circuit with device, switchboard, and revision
    circuit = db.query(Circuit).join(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        Circuit.circuit_id == circuit_id,
        Revision.user_id == user_id
    ).first()
    
    if not circuit:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    # Get measurement if exists (1:1 relationship)
    measurement = db.query(CircuitMeasurement).filter(
        CircuitMeasurement.circuit_id == circuit_id
    ).first()
    
    # Get terminal devices (1:N relationship)
    terminal_devices = db.query(TerminalDevice).filter(
        TerminalDevice.circuit_id == circuit_id
    ).all()
    
    return templates.TemplateResponse("circuit_detail.html", {
        "request": request,
        "circuit": circuit,
        "measurement": measurement,
        "terminal_devices": terminal_devices
    })


# UPDATE - Show edit form
@app.get("/circuit/{circuit_id}/edit", response_class=HTMLResponse)
async def circuit_edit_form(circuit_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Get circuit with verification
    circuit = db.query(Circuit).join(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        Circuit.circuit_id == circuit_id,
        Revision.user_id == user_id
    ).first()
    
    if not circuit:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    # Get dropdown configuration for circuit
    dropdown_config = get_field_dropdown_config("circuit", db)
    
    # PHASE 4: Get field configuration
    field_configs = get_entity_field_config('circuit', db)
    
    # Get all dropdown sources grouped by category
    categories = db.query(DropdownSource.category).distinct().all()
    dropdown_sources = {}
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    return templates.TemplateResponse("circuit_form.html", {
        "request": request,
        "device": circuit.device,
        "circuit": circuit,
        "is_edit": True,
        "dropdown_config": dropdown_config,
        "dropdown_sources": dropdown_sources,
        "field_configs": field_configs
    })


# UPDATE - Process form
@app.post("/circuit/{circuit_id}/update")
async def circuit_update(circuit_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Get circuit with verification
    circuit = db.query(Circuit).join(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        Circuit.circuit_id == circuit_id,
        Revision.user_id == user_id
    ).first()
    
    if not circuit:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    form_data = await request.form()
    
    def get_value(key, type_cast=None):
        value = form_data.get(key, "").strip()
        if not value:
            return None
        if type_cast == int:
            try:
                return int(value)
            except ValueError:
                return None
        elif type_cast == float:
            try:
                return float(value)
            except ValueError:
                return None
        return value
    
    # Update circuit fields
    circuit.circuit_number = get_value("circuit_number")
    circuit.circuit_room = get_value("circuit_room")
    circuit.circuit_description = get_value("circuit_description")
    circuit.circuit_description_from_switchboard = get_value("circuit_description_from_switchboard")
    circuit.circuit_number_of_outlets = get_value("circuit_number_of_outlets", int)
    circuit.circuit_cable_termination = get_value("circuit_cable_termination")
    circuit.circuit_cable = get_value("circuit_cable")
    circuit.circuit_cable_installation_method = get_value("circuit_cable_installation_method")
    
    db.commit()
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/circuit/{circuit_id}", status_code=303)


# DELETE
@app.post("/circuit/{circuit_id}/delete")
async def circuit_delete(circuit_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Verify ownership
    circuit = db.query(Circuit).join(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        Circuit.circuit_id == circuit_id,
        Revision.user_id == user_id
    ).first()
    
    if circuit:
        device_id = circuit.device_id
        # SQLAlchemy will handle cascade delete of measurements and terminal devices
        db.delete(circuit)
        db.commit()
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"/device/{device_id}", status_code=303)
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=303)


# ============================================================================
# CIRCUIT MEASUREMENT CRUD
# ============================================================================

# CREATE - Show form
@app.get("/circuit/{circuit_id}/measurement/create", response_class=HTMLResponse)
async def circuit_measurement_create_form(circuit_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Verify circuit ownership
    circuit = db.query(Circuit).join(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        Circuit.circuit_id == circuit_id,
        Revision.user_id == user_id
    ).first()
    
    if not circuit:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    # Check if measurement already exists (1:1)
    existing = db.query(CircuitMeasurement).filter(
        CircuitMeasurement.circuit_id == circuit_id
    ).first()
    
    if existing:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"/circuit/{circuit_id}/measurement/edit", status_code=303)
    
    return templates.TemplateResponse("circuit_measurement_form.html", {
        "request": request,
        "circuit": circuit,
        "measurement": None,
        "is_edit": False
    })


# CREATE - Process form
@app.post("/circuit/{circuit_id}/measurement/create")
async def circuit_measurement_create(circuit_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Verify circuit ownership
    circuit = db.query(Circuit).join(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        Circuit.circuit_id == circuit_id,
        Revision.user_id == user_id
    ).first()
    
    if not circuit:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    form_data = await request.form()
    
    def get_value(key, type_cast=None):
        value = form_data.get(key, "").strip()
        if not value:
            return None
        if type_cast == float:
            try:
                return float(value)
            except ValueError:
                return None
        return value
    
    # Create measurement
    new_measurement = CircuitMeasurement(
        circuit_id=circuit_id,
        measurements_circuit_insulation_resistance=get_value("measurements_circuit_insulation_resistance", float),
        measurements_circuit_loop_impedance_min=get_value("measurements_circuit_loop_impedance_min", float),
        measurements_circuit_loop_impedance_max=get_value("measurements_circuit_loop_impedance_max", float),
        measurements_circuit_rcd_trip_time_ms=get_value("measurements_circuit_rcd_trip_time_ms", float),
        measurements_circuit_rcd_test_current_ma=get_value("measurements_circuit_rcd_test_current_ma", float),
        measurements_circuit_earth_resistance=get_value("measurements_circuit_earth_resistance", float),
        measurements_circuit_continuity=get_value("measurements_circuit_continuity", float),
        measurements_circuit_order_of_phases=get_value("measurements_circuit_order_of_phases")
    )
    
    db.add(new_measurement)
    db.commit()
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/circuit/{circuit_id}", status_code=303)


# UPDATE - Show edit form
@app.get("/circuit/{circuit_id}/measurement/edit", response_class=HTMLResponse)
async def circuit_measurement_edit_form(circuit_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Verify circuit ownership
    circuit = db.query(Circuit).join(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        Circuit.circuit_id == circuit_id,
        Revision.user_id == user_id
    ).first()
    
    if not circuit:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    # Get measurement
    measurement = db.query(CircuitMeasurement).filter(
        CircuitMeasurement.circuit_id == circuit_id
    ).first()
    
    if not measurement:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"/circuit/{circuit_id}/measurement/create", status_code=303)
    
    return templates.TemplateResponse("circuit_measurement_form.html", {
        "request": request,
        "circuit": circuit,
        "measurement": measurement,
        "is_edit": True
    })


# UPDATE - Process form
@app.post("/circuit_measurement/{measurement_id}/update")
async def circuit_measurement_update(measurement_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Verify measurement ownership
    measurement = db.query(CircuitMeasurement).join(Circuit).join(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        CircuitMeasurement.measurement_id == measurement_id,
        Revision.user_id == user_id
    ).first()
    
    if not measurement:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    form_data = await request.form()
    
    def get_value(key, type_cast=None):
        value = form_data.get(key, "").strip()
        if not value:
            return None
        if type_cast == float:
            try:
                return float(value)
            except ValueError:
                return None
        return value
    
    # Update measurement fields
    measurement.measurements_circuit_insulation_resistance = get_value("measurements_circuit_insulation_resistance", float)
    measurement.measurements_circuit_loop_impedance_min = get_value("measurements_circuit_loop_impedance_min", float)
    measurement.measurements_circuit_loop_impedance_max = get_value("measurements_circuit_loop_impedance_max", float)
    measurement.measurements_circuit_rcd_trip_time_ms = get_value("measurements_circuit_rcd_trip_time_ms", float)
    measurement.measurements_circuit_rcd_test_current_ma = get_value("measurements_circuit_rcd_test_current_ma", float)
    measurement.measurements_circuit_earth_resistance = get_value("measurements_circuit_earth_resistance", float)
    measurement.measurements_circuit_continuity = get_value("measurements_circuit_continuity", float)
    measurement.measurements_circuit_order_of_phases = get_value("measurements_circuit_order_of_phases")
    
    db.commit()
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/circuit/{measurement.circuit_id}", status_code=303)


# DELETE
@app.post("/circuit_measurement/{measurement_id}/delete")
async def circuit_measurement_delete(measurement_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Verify ownership
    measurement = db.query(CircuitMeasurement).join(Circuit).join(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        CircuitMeasurement.measurement_id == measurement_id,
        Revision.user_id == user_id
    ).first()
    
    if measurement:
        circuit_id = measurement.circuit_id
        db.delete(measurement)
        db.commit()
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"/circuit/{circuit_id}", status_code=303)
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=303)



# === CIRCUIT QUICK ADD ENDPOINTS ===

@app.get("/device/{device_id}/circuit/list-with-form", response_class=HTMLResponse)
async def circuit_list_with_form(device_id: int, request: Request, db: Session = Depends(get_db)):
    """
    Returns the list of circuits + empty form container for HTMX
    """
    user_id = get_current_user(request)
    device = db.query(Device).join(Switchboard).join(Revision).filter(
        Device.device_id == device_id,
        Revision.user_id == user_id
    ).first()
    
    if not device:
        return "<div class='text-red-500 p-4'>Přístroj nenalezen</div>"
    
    # Get dropdown sources for form
    dropdown_sources = {}
    categories = db.query(DropdownSource.category).distinct().all()
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    return templates.TemplateResponse("components/circuit_list_with_form.html", {
        "request": request,
        "device_id": device_id,
        "circuits": device.circuits,
        "dropdown_sources": dropdown_sources,
        "show_form": False
    })


@app.get("/device/{device_id}/circuit/quick-add-form", response_class=HTMLResponse)
async def get_circuit_quick_add_form(
    device_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Returns HTML with inline form for adding circuit
    """
    user_id = get_current_user(request)
    
    # Verify device ownership
    device = db.query(Device).join(Switchboard).join(Revision).filter(
        Device.device_id == device_id,
        Revision.user_id == user_id
    ).first()
    
    if not device:
        return "<div class='text-red-500 p-4'>Přístroj nenalezen</div>"
    
    # Get dropdown sources for form
    dropdown_sources = {}
    categories = db.query(DropdownSource.category).distinct().all()
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    return templates.TemplateResponse("components/quick_add_circuit_form.html", {
        "request": request,
        "device_id": device_id,
        "dropdown_sources": dropdown_sources
    })


@app.post("/device/{device_id}/circuit/quick-add", response_class=HTMLResponse)
async def quick_add_circuit(
    device_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Creates new circuit and returns updated list + empty form
    """
    user_id = get_current_user(request)
    
    # Verify device ownership
    device = db.query(Device).join(Switchboard).join(Revision).filter(
        Device.device_id == device_id,
        Revision.user_id == user_id
    ).first()
    
    if not device:
        return "<div class='text-red-500 p-4'>Přístroj nenalezen</div>"
    
    form_data = await request.form()
    
    # Helper function
    def get_value(key, convert_type=None):
        value = form_data.get(key, "").strip()
        if not value:
            return None
        if convert_type == int:
            return int(value) if value else None
        if convert_type == float:
            return float(value) if value else None
        return value
    
    # Auto-determine order if not provided
    order = get_value("circuit_order", int)
    if order is None:
        max_order = db.query(func.max(Circuit.circuit_order)).filter(
            Circuit.device_id == device_id
        ).scalar()
        order = (max_order or 0) + 1
    
    # Create new circuit
    new_circuit = Circuit(
        device_id=device_id,
        circuit_name=get_value("circuit_name"),
        circuit_type=get_value("circuit_type"),
        circuit_order=order,
        circuit_description=get_value("circuit_description"),
        circuit_location=get_value("circuit_location"),
        circuit_cable_type=get_value("circuit_cable_type"),
        circuit_cable_cross_section=get_value("circuit_cable_cross_section", float),
        circuit_cable_length=get_value("circuit_cable_length", float),
        circuit_rated_current=get_value("circuit_rated_current", float),
        circuit_note=get_value("circuit_note")
    )
    
    db.add(new_circuit)
    db.commit()
    db.refresh(new_circuit)
    
    # Return updated list + empty form
    device = db.query(Device).filter(Device.device_id == device_id).first()
    
    # Get dropdown sources for form
    dropdown_sources = {}
    categories = db.query(DropdownSource.category).distinct().all()
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    return templates.TemplateResponse("components/circuit_list_with_form.html", {
        "request": request,
        "device_id": device_id,
        "circuits": device.circuits,
        "dropdown_sources": dropdown_sources,
        "show_form": False  # Hide form after successful submit
    })


# ============================================================================
# DEVICE DETAIL (for showing circuits)
# ============================================================================

@app.get("/device/{device_id}", response_class=HTMLResponse)
async def device_detail(device_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Get device with switchboard and revision
    device = db.query(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        SwitchboardDevice.device_id == device_id,
        Revision.user_id == user_id
    ).first()
    
    if not device:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    # Get circuits for this device
    circuits = db.query(Circuit).filter(
        Circuit.device_id == device_id
    ).all()
    
    return templates.TemplateResponse("device_detail.html", {
        "request": request,
        "device": device,
        "circuits": circuits,
        "sidebar_revisions": get_sidebar_revisions(db, user_id),
        "current_revision_for_sidebar": device.switchboard.revision
    })


# === TERMINAL DEVICE QUICK ADD ENDPOINTS ===

@app.get("/circuit/{circuit_id}/terminal/list-with-form", response_class=HTMLResponse)
async def terminal_list_with_form(circuit_id: int, request: Request, db: Session = Depends(get_db)):
    """
    Returns the list of terminal devices + empty form container for HTMX
    """
    user_id = get_current_user(request)
    circuit = db.query(Circuit).join(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        Circuit.circuit_id == circuit_id,
        Revision.user_id == user_id
    ).first()
    
    if not circuit:
        return "<div class='text-red-500 p-4'>Obvod nenalezen</div>"
    
    # Get dropdown sources for form
    dropdown_sources = {}
    categories = db.query(DropdownSource.category).distinct().all()
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    return templates.TemplateResponse("components/terminal_list_with_form.html", {
        "request": request,
        "circuit_id": circuit_id,
        "terminal_devices": circuit.terminal_devices,
        "dropdown_sources": dropdown_sources,
        "show_form": False
    })


@app.get("/circuit/{circuit_id}/terminal/quick-add-form", response_class=HTMLResponse)
async def get_terminal_quick_add_form(
    circuit_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Returns HTML with inline form for adding terminal device
    """
    user_id = get_current_user(request)
    
    # Verify circuit ownership
    circuit = db.query(Circuit).join(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        Circuit.circuit_id == circuit_id,
        Revision.user_id == user_id
    ).first()
    
    if not circuit:
        return "<div class='text-red-500 p-4'>Obvod nenalezen</div>"
    
    # Get dropdown sources for form
    dropdown_sources = {}
    categories = db.query(DropdownSource.category).distinct().all()
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    return templates.TemplateResponse("components/quick_add_terminal_form.html", {
        "request": request,
        "circuit_id": circuit_id,
        "dropdown_sources": dropdown_sources
    })


@app.post("/circuit/{circuit_id}/terminal/quick-add", response_class=HTMLResponse)
async def quick_add_terminal(
    circuit_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Creates new terminal device and returns updated list + empty form
    """
    user_id = get_current_user(request)
    
    # Verify circuit ownership
    circuit = db.query(Circuit).join(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        Circuit.circuit_id == circuit_id,
        Revision.user_id == user_id
    ).first()
    
    if not circuit:
        return "<div class='text-red-500 p-4'>Obvod nenalezen</div>"
    
    form_data = await request.form()
    
    # Helper function
    def get_value(key, convert_type=None):
        value = form_data.get(key, "").strip()
        if not value:
            return None
        if convert_type == int:
            return int(value) if value else None
        if convert_type == float:
            return float(value) if value else None
        return value
    
    # Create new terminal device
    new_terminal = TerminalDevice(
        circuit_id=circuit_id,
        terminal_device_type=get_value("terminal_device_type"),
        terminal_device_manufacturer=get_value("terminal_device_manufacturer"),
        terminal_device_model=get_value("terminal_device_model"),
        terminal_device_marking=get_value("terminal_device_marking"),
        terminal_device_power=get_value("terminal_device_power", float),
        terminal_device_ip_rating=get_value("terminal_device_ip_rating"),
        terminal_device_protection_class=get_value("terminal_device_protection_class"),
        terminal_device_serial_number=get_value("terminal_device_serial_number"),
        terminal_device_supply_type=get_value("terminal_device_supply_type"),
        terminal_device_installation_method=get_value("terminal_device_installation_method")
    )
    
    db.add(new_terminal)
    db.commit()
    db.refresh(new_terminal)
    
    # Return updated list + empty form
    circuit = db.query(Circuit).filter(Circuit.circuit_id == circuit_id).first()
    
    # Get dropdown sources for form
    dropdown_sources = {}
    categories = db.query(DropdownSource.category).distinct().all()
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    return templates.TemplateResponse("components/terminal_list_with_form.html", {
        "request": request,
        "circuit_id": circuit_id,
        "terminal_devices": circuit.terminal_devices,
        "dropdown_sources": dropdown_sources,
        "show_form": False  # Hide form after successful submit
    })


# ============================================================================
# TERMINAL DEVICE CRUD
# ============================================================================

# CREATE - Show form
@app.get("/circuit/{circuit_id}/terminal/create", response_class=HTMLResponse)
async def terminal_device_create_form(circuit_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Verify circuit ownership through device → switchboard → revision
    circuit = db.query(Circuit).join(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        Circuit.circuit_id == circuit_id,
        Revision.user_id == user_id
    ).first()
    
    if not circuit:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    # Get dropdown configuration for terminal_device
    dropdown_config = get_field_dropdown_config("terminal_device", db)
    
    # PHASE 4: Get field configuration
    field_configs = get_entity_field_config('terminal_device', db)
    
    # Get all dropdown sources grouped by category
    categories = db.query(DropdownSource.category).distinct().all()
    dropdown_sources = {}
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    return templates.TemplateResponse("terminal_device_form.html", {
        "request": request,
        "circuit": circuit,
        "terminal_device": None,
        "is_edit": False,
        "dropdown_config": dropdown_config,
        "dropdown_sources": dropdown_sources,
        "field_configs": field_configs
    })


# CREATE - Process form
@app.post("/circuit/{circuit_id}/terminal/create")
async def terminal_device_create(circuit_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Verify circuit ownership
    circuit = db.query(Circuit).join(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        Circuit.circuit_id == circuit_id,
        Revision.user_id == user_id
    ).first()
    
    if not circuit:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    form_data = await request.form()
    
    def get_value(key, type_cast=None):
        value = form_data.get(key, "").strip()
        if not value:
            return None
        if type_cast == float:
            try:
                return float(value)
            except ValueError:
                return None
        return value
    
    # Create terminal device
    new_terminal = TerminalDevice(
        circuit_id=circuit_id,
        terminal_device_type=get_value("terminal_device_type"),
        terminal_device_manufacturer=get_value("terminal_device_manufacturer"),
        terminal_device_model=get_value("terminal_device_model"),
        terminal_device_marking=get_value("terminal_device_marking"),
        terminal_device_power=get_value("terminal_device_power", float),
        terminal_device_ip_rating=get_value("terminal_device_ip_rating"),
        terminal_device_protection_class=get_value("terminal_device_protection_class"),
        terminal_device_serial_number=get_value("terminal_device_serial_number"),
        terminal_device_supply_type=get_value("terminal_device_supply_type"),
        terminal_device_installation_method=get_value("terminal_device_installation_method")
    )
    
    db.add(new_terminal)
    db.commit()
    db.refresh(new_terminal)
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/circuit/{circuit_id}", status_code=303)


# READ - Terminal device detail
@app.get("/terminal/{terminal_device_id}", response_class=HTMLResponse)
async def terminal_device_detail(terminal_device_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Get terminal device with circuit, device, switchboard, and revision
    terminal = db.query(TerminalDevice).join(Circuit).join(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        TerminalDevice.terminal_device_id == terminal_device_id,
        Revision.user_id == user_id
    ).first()
    
    if not terminal:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    return templates.TemplateResponse("terminal_device_detail.html", {
        "request": request,
        "terminal": terminal
    })


# UPDATE - Show edit form
@app.get("/terminal/{terminal_device_id}/edit", response_class=HTMLResponse)
async def terminal_device_edit_form(terminal_device_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Get terminal device with verification
    terminal = db.query(TerminalDevice).join(Circuit).join(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        TerminalDevice.terminal_device_id == terminal_device_id,
        Revision.user_id == user_id
    ).first()
    
    if not terminal:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    # Get dropdown configuration for terminal_device
    dropdown_config = get_field_dropdown_config("terminal_device", db)
    
    # PHASE 4: Get field configuration
    field_configs = get_entity_field_config('terminal_device', db)
    
    # Get all dropdown sources grouped by category
    categories = db.query(DropdownSource.category).distinct().all()
    dropdown_sources = {}
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    return templates.TemplateResponse("terminal_device_form.html", {
        "request": request,
        "circuit": terminal.circuit,
        "terminal_device": terminal,
        "is_edit": True,
        "dropdown_config": dropdown_config,
        "dropdown_sources": dropdown_sources,
        "field_configs": field_configs
    })


# UPDATE - Process form
@app.post("/terminal/{terminal_device_id}/update")
async def terminal_device_update(terminal_device_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Get terminal device with verification
    terminal = db.query(TerminalDevice).join(Circuit).join(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        TerminalDevice.terminal_device_id == terminal_device_id,
        Revision.user_id == user_id
    ).first()
    
    if not terminal:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    form_data = await request.form()
    
    def get_value(key, type_cast=None):
        value = form_data.get(key, "").strip()
        if not value:
            return None
        if type_cast == float:
            try:
                return float(value)
            except ValueError:
                return None
        return value
    
    # Update terminal device fields
    terminal.terminal_device_type = get_value("terminal_device_type")
    terminal.terminal_device_manufacturer = get_value("terminal_device_manufacturer")
    terminal.terminal_device_model = get_value("terminal_device_model")
    terminal.terminal_device_marking = get_value("terminal_device_marking")
    terminal.terminal_device_power = get_value("terminal_device_power", float)
    terminal.terminal_device_ip_rating = get_value("terminal_device_ip_rating")
    terminal.terminal_device_protection_class = get_value("terminal_device_protection_class")
    terminal.terminal_device_serial_number = get_value("terminal_device_serial_number")
    terminal.terminal_device_supply_type = get_value("terminal_device_supply_type")
    terminal.terminal_device_installation_method = get_value("terminal_device_installation_method")
    
    db.commit()
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/circuit/{terminal.circuit_id}", status_code=303)


# DELETE
@app.post("/terminal/{terminal_device_id}/delete")
async def terminal_device_delete(terminal_device_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Verify ownership
    terminal = db.query(TerminalDevice).join(Circuit).join(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        TerminalDevice.terminal_device_id == terminal_device_id,
        Revision.user_id == user_id
    ).first()
    
    if terminal:
        circuit_id = terminal.circuit_id
        db.delete(terminal)
        db.commit()
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"/circuit/{circuit_id}", status_code=303)
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=303)


# Duplicate
@app.post("/terminal/{terminal_device_id}/duplicate")
async def terminal_device_duplicate(terminal_device_id: int, request: Request, db: Session = Depends(get_db)):
    from fastapi.responses import RedirectResponse
    
    user_id = get_current_user(request)
    original = db.query(TerminalDevice).join(Circuit).join(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        TerminalDevice.terminal_device_id == terminal_device_id,
        Revision.user_id == user_id
    ).first()
    
    if not original:
        return RedirectResponse(url="/", status_code=303)
    
    # Create duplicate terminal device
    new_terminal = TerminalDevice(
        circuit_id=original.circuit_id,
        terminal_device_type=original.terminal_device_type,
        terminal_device_manufacturer=original.terminal_device_manufacturer,
        terminal_device_model=original.terminal_device_model,
        terminal_device_marking=f"{original.terminal_device_marking or ''} (kopie)" if original.terminal_device_marking else "Kopie",
        terminal_device_power=original.terminal_device_power,
        terminal_device_ip_rating=original.terminal_device_ip_rating,
        terminal_device_protection_class=original.terminal_device_protection_class,
        terminal_device_serial_number=original.terminal_device_serial_number,
        terminal_device_supply_type=original.terminal_device_supply_type,
        terminal_device_installation_method=original.terminal_device_installation_method
    )
    db.add(new_terminal)
    db.commit()
    
    return RedirectResponse(url=f"/terminal/{new_terminal.terminal_device_id}", status_code=303)


# ============================================================================
# DROPDOWN SYSTEM & SETTINGS
# ============================================================================

# Settings page - Dropdown management
@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Get all dropdown categories (distinct)
    categories = db.query(DropdownSource.category).distinct().order_by(DropdownSource.category).all()
    categories = [cat[0] for cat in categories]
    
    # Get all dropdown sources grouped by category
    dropdown_sources = {}
    for category in categories:
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    # Get dropdown configurations
    dropdown_configs = db.query(DropdownConfig).all()
    
    # Create dict for easy lookup of existing configs
    configs_dict = {}
    for config in dropdown_configs:
        key = f"{config.entity_type}_{config.field_name}"
        configs_dict[key] = config
    
    # ✅ PHASE 4: Get configurable fields from database (not hardcoded!)
    # DŮLEŽITÉ: Poskytujeme OBOJE struktury pro kompatibilitu
    
    # Dict struktura (entity -> field_name -> label)
    configurable_fields = {}
    for config in dropdown_configs:
        entity = config.entity_type
        if entity not in configurable_fields:
            configurable_fields[entity] = {}
        
        label = config.custom_label if config.custom_label else config.field_label
        configurable_fields[entity][config.field_name] = label
    
    # List struktura (pro případy kde template iteruje přes list)
    field_configs_list = []
    for config in dropdown_configs:
        label = config.custom_label if config.custom_label else config.field_label
        field_configs_list.append({
            'id': config.id,
            'entity_type': config.entity_type,
            'name': config.field_name,
            'label': label,
            'enabled': config.enabled,
            'category': config.field_category,
            'required': config.is_required,
            'display_order': config.display_order,
            'dropdown_enabled': config.dropdown_enabled,
            'dropdown_category': config.dropdown_category
        })
    
    # DEBUG: Print pro diagnostiku
    print(f"🔍 DEBUG Settings: configurable_fields má {len(configurable_fields)} entit")
    for entity, fields in configurable_fields.items():
        print(f"  - {entity}: {len(fields)} polí")
    print(f"🔍 DEBUG Settings: field_configs_list má {len(field_configs_list)} položek")
    
    return templates.TemplateResponse("settings_redesigned.html", {
        "request": request,
        "categories": categories,
        "dropdown_sources": dropdown_sources,
        "dropdown_configs": dropdown_configs,
        "configs_dict": configs_dict,
        "configurable_fields": configurable_fields,  # Dict struktura
        "field_configs": field_configs_list,  # List struktura (backup)
        "sidebar_revisions": get_sidebar_revisions(db, user_id)
    })


# Add new dropdown category
@app.post("/settings/dropdown/category/create")
async def dropdown_category_create(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    form_data = await request.form()
    
    category = form_data.get("category", "").strip()
    
    if category:
        # Check if category already exists
        existing = db.query(DropdownSource).filter(DropdownSource.category == category).first()
        if not existing:
            # Create first item in new category
            new_source = DropdownSource(
                category=category,
                value="Nová hodnota",
                display_order=0
            )
            db.add(new_source)
            db.commit()
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/settings", status_code=303)


# Add new dropdown value to existing category
@app.post("/settings/dropdown/value/create")
async def dropdown_value_create(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    form_data = await request.form()
    
    category = form_data.get("category", "").strip()
    value = form_data.get("value", "").strip()
    
    if category and value:
        # Get max display_order for this category
        max_order = db.query(func.max(DropdownSource.display_order)).filter(
            DropdownSource.category == category
        ).scalar() or 0
        
        new_source = DropdownSource(
            category=category,
            value=value,
            display_order=max_order + 1
        )
        db.add(new_source)
        db.commit()
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/settings", status_code=303)


# Update dropdown value
@app.post("/settings/dropdown/value/{value_id}/update")
async def dropdown_value_update(value_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    form_data = await request.form()
    
    source = db.query(DropdownSource).filter(DropdownSource.id == value_id).first()
    if source:
        new_value = form_data.get("value", "").strip()
        if new_value:
            source.value = new_value
            db.commit()
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/settings", status_code=303)


# Delete dropdown value
@app.post("/settings/dropdown/value/{value_id}/delete")
async def dropdown_value_delete(value_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    source = db.query(DropdownSource).filter(DropdownSource.id == value_id).first()
    if source:
        db.delete(source)
        db.commit()
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/settings", status_code=303)


# Move dropdown value up
@app.post("/settings/dropdown/value/{value_id}/move-up")
async def dropdown_value_move_up(value_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    source = db.query(DropdownSource).filter(DropdownSource.id == value_id).first()
    if source and source.display_order > 0:
        # Find item with previous order
        prev_source = db.query(DropdownSource).filter(
            DropdownSource.category == source.category,
            DropdownSource.display_order == source.display_order - 1
        ).first()
        
        if prev_source:
            # Swap orders
            source.display_order, prev_source.display_order = prev_source.display_order, source.display_order
            db.commit()
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/settings", status_code=303)


# Move dropdown value down
@app.post("/settings/dropdown/value/{value_id}/move-down")
async def dropdown_value_move_down(value_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    source = db.query(DropdownSource).filter(DropdownSource.id == value_id).first()
    if source:
        # Find item with next order
        next_source = db.query(DropdownSource).filter(
            DropdownSource.category == source.category,
            DropdownSource.display_order == source.display_order + 1
        ).first()
        
        if next_source:
            # Swap orders
            source.display_order, next_source.display_order = next_source.display_order, source.display_order
            db.commit()
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/settings", status_code=303)


# HTMX endpoint - Get dropdown values for a category (for inline widget)
@app.get("/api/dropdown/{category}")
async def get_dropdown_values(category: str, db: Session = Depends(get_db)):
    sources = db.query(DropdownSource).filter(
        DropdownSource.category == category
    ).order_by(DropdownSource.display_order, DropdownSource.value).all()
    
    return {"values": [{"id": s.id, "value": s.value} for s in sources]}


# HTMX endpoint - Add new value to dropdown (inline from form)
@app.post("/api/dropdown/{category}/add")
async def add_dropdown_value_inline(category: str, request: Request, db: Session = Depends(get_db)):
    form_data = await request.form()
    value = form_data.get("value", "").strip()
    
    if value:
        # Get max display_order for this category
        max_order = db.query(func.max(DropdownSource.display_order)).filter(
            DropdownSource.category == category
        ).scalar() or 0
        
        new_source = DropdownSource(
            category=category,
            value=value,
            display_order=max_order + 1
        )
        db.add(new_source)
        db.commit()
        db.refresh(new_source)
        
        return {"success": True, "id": new_source.id, "value": new_source.value}
    
    return {"success": False, "error": "Value is required"}


# API endpoint for dropdown_widget_compact.html
@app.post("/api/dropdown/{category}/add")
async def add_dropdown_value_api(category: str, request: Request, db: Session = Depends(get_db)):
    """API endpoint specifically for dropdown_widget_compact.html modal"""
    form_data = await request.form()
    value = form_data.get("value", "").strip()
    
    if value:
        # Get max display_order for this category
        max_order = db.query(func.max(DropdownSource.display_order)).filter(
            DropdownSource.category == category
        ).scalar() or 0
        
        new_source = DropdownSource(
            category=category,
            value=value,
            display_order=max_order + 1
        )
        db.add(new_source)
        db.commit()
        db.refresh(new_source)
        
        return {"success": True, "id": new_source.id, "value": new_source.value}
    
    return {"success": False, "error": "Value is required"}


# Update dropdown configuration
@app.post("/settings/dropdown-config/update")
async def dropdown_config_update(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    form_data = await request.form()
    
    entity_type = form_data.get("entity_type", "").strip()
    field_name = form_data.get("field_name", "").strip()
    dropdown_enabled = form_data.get("dropdown_enabled") == "on"
    dropdown_category = form_data.get("dropdown_category", "").strip() or None
    
    # 🔧 BUGFIX: If dropdown is enabled but no category selected, disable it
    if dropdown_enabled and not dropdown_category:
        dropdown_enabled = False
    
    if entity_type and field_name:
        # Check if config exists
        config = db.query(DropdownConfig).filter(
            DropdownConfig.entity_type == entity_type,
            DropdownConfig.field_name == field_name
        ).first()
        
        if config:
            config.dropdown_enabled = dropdown_enabled
            config.dropdown_category = dropdown_category
        else:
            config = DropdownConfig(
                entity_type=entity_type,
                field_name=field_name,
                dropdown_enabled=dropdown_enabled,
                dropdown_category=dropdown_category
            )
            db.add(config)
        
        db.commit()
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/settings", status_code=303)


# ========================================
# PHASE 4: FIELD VISIBILITY CONFIGURATION
# ========================================

# Get form field configuration for an entity type
@app.get("/api/form-config/{entity_type}")
async def get_form_config(entity_type: str, db: Session = Depends(get_db)):
    """
    Returns field configuration for a given entity type
    Only includes enabled fields, ordered by display_order
    """
    fields = db.query(DropdownConfig).filter(
        DropdownConfig.entity_type == entity_type,
        DropdownConfig.enabled == True
    ).order_by(DropdownConfig.display_order).all()
    
    return {
        "entity_type": entity_type,
        "fields": [
            {
                "name": f.field_name,
                "label": f.field_label,
                "type": f.field_type,
                "required": f.is_required,
                "category": f.field_category,
                "has_dropdown": f.dropdown_enabled,
                "dropdown_category": f.dropdown_category
            }
            for f in fields
        ]
    }


# Get all field configurations for an entity (for settings page)
@app.get("/api/field-config/{entity_type}/all")
async def get_all_field_config(entity_type: str, db: Session = Depends(get_db)):
    """
    Returns ALL field configurations for an entity (including disabled)
    For settings/configuration page
    PHASE 4.5: Includes custom_label and category
    """
    fields = db.query(DropdownConfig).filter(
        DropdownConfig.entity_type == entity_type
    ).order_by(DropdownConfig.field_category, DropdownConfig.display_order).all()
    
    # Group by category
    by_category = {}
    for field in fields:
        category = field.field_category or 'uncategorized'
        if category not in by_category:
            by_category[category] = []
        
        # PHASE 4.5: Include custom_label
        display_label = field.custom_label if field.custom_label else field.field_label
        
        by_category[category].append({
            "id": field.id,
            "name": field.field_name,
            "label": display_label,
            "type": field.field_type,
            "enabled": field.enabled,
            "required": field.is_required,
            "display_order": field.display_order,
            "has_dropdown": field.dropdown_enabled,
            "dropdown_category": field.dropdown_category,
            "category": field.field_category,  # PHASE 4.5
            "custom_label": field.custom_label  # PHASE 4.5
        })
    
    return {
        "entity_type": entity_type,
        "fields_by_category": by_category
    }


# Update field configuration (enable/disable, reorder)
@app.post("/settings/field-config/update")
async def field_config_update(request: Request, db: Session = Depends(get_db)):
    """
    Update field configuration (visibility and order)
    Receives form data with field IDs and their new states
    """
    user_id = get_current_user(request)
    form_data = await request.form()
    
    # Process each field configuration
    for key, value in form_data.items():
        if key.startswith('field_enabled_'):
            # Extract field ID
            field_id = int(key.replace('field_enabled_', ''))
            enabled = value == 'on'
            
            # Update config
            config = db.query(DropdownConfig).filter(
                DropdownConfig.id == field_id
            ).first()
            
            if config and not config.is_required:  # Can't disable required fields
                config.enabled = enabled
        
        elif key.startswith('field_order_'):
            # Extract field ID
            field_id = int(key.replace('field_order_', ''))
            try:
                display_order = int(value)
                
                config = db.query(DropdownConfig).filter(
                    DropdownConfig.id == field_id
                ).first()
                
                if config:
                    config.display_order = display_order
            except ValueError:
                pass
    
    db.commit()
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/settings#field-visibility", status_code=303)


# Toggle single field visibility (for AJAX)
@app.post("/settings/field/toggle")
async def field_toggle(request: Request, db: Session = Depends(get_db)):
    """Toggle field visibility via AJAX"""
    user_id = get_current_user(request)
    form_data = await request.form()
    
    field_id = int(form_data.get('field_id'))
    enabled = form_data.get('enabled') == 'true'
    
    config = db.query(DropdownConfig).filter(
        DropdownConfig.id == field_id
    ).first()
    
    if config and not config.is_required:
        config.enabled = enabled
        db.commit()
        return {"success": True, "enabled": enabled}
    
    return {"success": False, "error": "Field not found or is required"}


# Bulk update field visibility for entity
@app.post("/settings/field-config/{entity_type}/bulk-update")
async def field_config_bulk_update(
    entity_type: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Bulk update field configurations for an entity
    Used for quick enable/disable all additional fields
    """
    user_id = get_current_user(request)
    form_data = await request.form()
    
    action = form_data.get("action")  # 'enable_all' or 'disable_all' or 'reset_defaults'
    
    if action == "enable_all":
        # Enable all additional (non-required) fields
        db.query(DropdownConfig).filter(
            DropdownConfig.entity_type == entity_type,
            DropdownConfig.is_required == False
        ).update({"enabled": True})
        
    elif action == "disable_all":
        # Disable all additional (non-required) fields
        db.query(DropdownConfig).filter(
            DropdownConfig.entity_type == entity_type,
            DropdownConfig.is_required == False
        ).update({"enabled": False})
        
    elif action == "reset_defaults":
        # Reset to default configuration (from seed data)
        # This would need to be implemented based on your defaults
        pass
    
    db.commit()
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/settings#field-visibility", status_code=303)


# ========================================
# PHASE 4.5: ADVANCED FIELD CONFIGURATION
# ========================================

# Rename field (custom label)
@app.post("/settings/field-config/{field_id}/rename")
async def field_config_rename(
    field_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Update custom label for a field
    """
    user_id = get_current_user(request)
    form_data = await request.form()
    
    custom_label = form_data.get("custom_label", "").strip()
    
    config = db.query(DropdownConfig).filter(
        DropdownConfig.id == field_id
    ).first()
    
    if config:
        # If custom_label is empty, set to None to use default label
        config.custom_label = custom_label if custom_label else None
        db.commit()
        return {"success": True, "custom_label": config.custom_label}
    
    return {"success": False, "error": "Field not found"}


# Change field category
@app.post("/settings/field-config/{field_id}/change-category")
async def field_config_change_category(
    field_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Change the category of a field
    """
    user_id = get_current_user(request)
    form_data = await request.form()
    
    new_category = form_data.get("category", "").strip()
    
    config = db.query(DropdownConfig).filter(
        DropdownConfig.id == field_id
    ).first()
    
    if config:
        config.field_category = new_category
        db.commit()
        return {"success": True, "category": new_category}
    
    return {"success": False, "error": "Field not found"}


# 🔧 NEW: Reorder fields within same category
@app.post("/settings/field-config/reorder")
async def field_config_reorder(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Reorder fields within a category
    Accepts array of field IDs in new order
    """
    user_id = get_current_user(request)
    data = await request.json()
    
    entity_type = data.get("entity_type")
    category = data.get("category")
    field_order = data.get("field_order", [])  # Array of field IDs
    
    if not entity_type or not category or not field_order:
        return {"success": False, "error": "Missing parameters"}
    
    try:
        # Update display_order for each field
        for index, field_id in enumerate(field_order):
            config = db.query(DropdownConfig).filter(
                DropdownConfig.id == field_id,
                DropdownConfig.entity_type == entity_type,
                DropdownConfig.field_category == category
            ).first()
            
            if config:
                config.display_order = (index + 1) * 10  # 10, 20, 30, ...
        
        db.commit()
        return {"success": True, "message": "Pořadí aktualizováno"}
    
    except Exception as e:
        db.rollback()
        return {"success": False, "error": str(e)}


# 🔧 NEW: Rename field (custom label)
@app.post("/settings/field-config/{field_id}/rename")
async def field_config_rename(
    field_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Rename a field by setting custom_label
    """
    user_id = get_current_user(request)
    form_data = await request.form()
    
    custom_label = form_data.get("custom_label", "").strip()
    
    config = db.query(DropdownConfig).filter(
        DropdownConfig.id == field_id
    ).first()
    
    if not config:
        return {"success": False, "error": "Field not found"}
    
    # Empty custom_label means reset to default
    config.custom_label = custom_label if custom_label else None
    db.commit()
    
    final_label = custom_label if custom_label else config.field_label
    return {"success": True, "label": final_label}


# 🔧 IMPROVED: Edit dropdown value (was missing)
@app.post("/settings/dropdown/value/{value_id}/edit")
async def dropdown_value_edit(
    value_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Edit existing dropdown value
    """
    user_id = get_current_user(request)
    form_data = await request.form()
    
    new_value = form_data.get("value", "").strip()
    
    if not new_value:
        return {"success": False, "error": "Value cannot be empty"}
    
    source = db.query(DropdownSource).filter(
        DropdownSource.id == value_id
    ).first()
    
    if not source:
        return {"success": False, "error": "Value not found"}
    
    source.value = new_value
    db.commit()
    
    return {"success": True, "value": new_value}


# 🔧 NEW: Move field up in order
@app.post("/settings/field-config/{field_id}/move-up")
async def field_config_move_up(field_id: int, request: Request, db: Session = Depends(get_db)):
    """Move field up in display order within its category"""
    user_id = get_current_user(request)
    
    field = db.query(DropdownConfig).filter(DropdownConfig.id == field_id).first()
    if not field:
        return {"success": False, "error": "Field not found"}
    
    # Find previous field in same entity + category
    prev_field = db.query(DropdownConfig).filter(
        DropdownConfig.entity_type == field.entity_type,
        DropdownConfig.field_category == field.field_category,
        DropdownConfig.display_order < field.display_order
    ).order_by(DropdownConfig.display_order.desc()).first()
    
    if prev_field:
        # Swap display orders
        field.display_order, prev_field.display_order = prev_field.display_order, field.display_order
        db.commit()
        return {"success": True, "message": "Pole přesunuto nahoru"}
    
    return {"success": False, "error": "Pole je již první"}


# 🔧 NEW: Move field down in order
@app.post("/settings/field-config/{field_id}/move-down")
async def field_config_move_down(field_id: int, request: Request, db: Session = Depends(get_db)):
    """Move field down in display order within its category"""
    user_id = get_current_user(request)
    
    field = db.query(DropdownConfig).filter(DropdownConfig.id == field_id).first()
    if not field:
        return {"success": False, "error": "Field not found"}
    
    # Find next field in same entity + category
    next_field = db.query(DropdownConfig).filter(
        DropdownConfig.entity_type == field.entity_type,
        DropdownConfig.field_category == field.field_category,
        DropdownConfig.display_order > field.display_order
    ).order_by(DropdownConfig.display_order.asc()).first()
    
    if next_field:
        # Swap display orders
        field.display_order, next_field.display_order = next_field.display_order, field.display_order
        db.commit()
        return {"success": True, "message": "Pole přesunuto dolů"}
    
    return {"success": False, "error": "Pole je již poslední"}


# Get all categories for entity
@app.get("/api/field-categories/{entity_type}")
async def get_field_categories(
    entity_type: str,
    db: Session = Depends(get_db)
):
    """
    Get all categories for a specific entity type
    """
    from models import FieldCategory
    
    categories = db.query(FieldCategory).filter(
        FieldCategory.entity_type == entity_type
    ).order_by(FieldCategory.display_order).all()
    
    return {
        "entity_type": entity_type,
        "categories": [
            {
                "id": c.id,
                "key": c.category_key,
                "label": c.category_label,
                "icon": c.icon,
                "order": c.display_order
            }
            for c in categories
        ]
    }


# Create new category
@app.post("/api/field-categories/create")
async def create_field_category(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Create a new field category for an entity
    """
    user_id = get_current_user(request)
    form_data = await request.form()
    
    from models import FieldCategory
    
    entity_type = form_data.get("entity_type", "").strip()
    category_key = form_data.get("category_key", "").strip()
    category_label = form_data.get("category_label", "").strip()
    icon = form_data.get("icon", "📋").strip()
    
    if not entity_type or not category_key or not category_label:
        return {"success": False, "error": "Missing required fields"}
    
    # Check if category already exists
    existing = db.query(FieldCategory).filter(
        FieldCategory.entity_type == entity_type,
        FieldCategory.category_key == category_key
    ).first()
    
    if existing:
        return {"success": False, "error": "Category already exists"}
    
    # Get max display order
    max_order = db.query(func.max(FieldCategory.display_order)).filter(
        FieldCategory.entity_type == entity_type
    ).scalar() or 0
    
    # Create new category
    new_category = FieldCategory(
        entity_type=entity_type,
        category_key=category_key,
        category_label=category_label,
        icon=icon,
        display_order=max_order + 10
    )
    
    db.add(new_category)
    db.commit()
    
    return {
        "success": True,
        "category": {
            "id": new_category.id,
            "key": new_category.category_key,
            "label": new_category.category_label,
            "icon": new_category.icon
        }
    }


# Delete category
@app.post("/api/field-categories/{category_id}/delete")
async def delete_field_category(
    category_id: int,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Delete a field category
    Fields in this category will be moved to 'additional'
    """
    user_id = get_current_user(request)
    
    from models import FieldCategory
    
    category = db.query(FieldCategory).filter(
        FieldCategory.id == category_id
    ).first()
    
    if not category:
        return {"success": False, "error": "Category not found"}
    
    category_key = category.category_key
    entity_type = category.entity_type
    
    # Move all fields from this category to 'additional'
    db.query(DropdownConfig).filter(
        DropdownConfig.entity_type == entity_type,
        DropdownConfig.field_category == category_key
    ).update({"field_category": "additional"})
    
    # Delete category
    db.delete(category)
    db.commit()
    
    return {"success": True}


# ========================================
# PROFILE PAGE
# ========================================

@app.get("/profile", response_class=HTMLResponse)
async def profile_page(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Simple profile page showing user info
    """
    user_id = get_current_user(request)
    
    # Count user's revisions
    total_revisions = db.query(Revision).filter(Revision.user_id == user_id).count()
    
    # Count total switchboards
    total_switchboards = db.query(Switchboard).join(Revision).filter(
        Revision.user_id == user_id
    ).count()
    
    # Count total devices
    total_devices = db.query(Device).join(Switchboard).join(Revision).filter(
        Revision.user_id == user_id
    ).count()
    
    # Get sidebar revisions
    sidebar_revisions = get_sidebar_revisions(db, user_id)
    
    return templates.TemplateResponse("profile.html", {
        "request": request,
        "user_id": user_id,
        "total_revisions": total_revisions,
        "total_switchboards": total_switchboards,
        "total_devices": total_devices,
        "sidebar_revisions": sidebar_revisions
    })


# ========================================
# QUICK ENTRY MODAL ENDPOINTS (Phase 2)
# ========================================

@app.get("/api/quick-entry/step1", response_class=HTMLResponse)
async def quick_entry_step1_get(
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Vrátí HTML pro krok 1 - základní info revize
    PHASE 4.5: Uses field_configs for dynamic form rendering
    """
    user_id = get_current_user(request)
    
    # Get field configuration for Revision (basic fields only)
    field_configs = get_entity_field_config('revision', db)
    basic_fields = [f for f in field_configs if f.get('category') == 'basic' and f.get('enabled')]
    
    return templates.TemplateResponse("modals/quick_entry_step1.html", {
        "request": request,
        "field_configs": basic_fields
    })


@app.post("/api/quick-entry/step1", response_class=HTMLResponse)
async def quick_entry_step1_post(
    request: Request,
    db: Session = Depends(get_db),
    revision_name: str = Form(...),
    revision_client: str = Form(...),
    revision_address: str = Form(...),
    revision_code: str = Form(None),
    revision_start_date: str = Form(None),
    revision_type: str = Form(None),
    revision_technician: str = Form(None),
    revision_description: str = Form(None)
):
    """
    Uloží základní info revize do session
    Vrátí HTML pro krok 2 - přidání rozváděčů
    PHASE 4.5: Uses field_configs for switchboard fields
    """
    user_id = get_current_user(request)
    
    # Uložení do session
    request.session['temp_revision'] = {
        'revision_name': revision_name,
        'revision_client': revision_client,
        'revision_address': revision_address,
        'revision_code': revision_code,
        'revision_start_date': revision_start_date,
        'revision_type': revision_type,
        'revision_technician': revision_technician,
        'revision_description': revision_description
    }
    
    # PHASE 4.5: Get field configuration for Switchboard (basic fields only)
    field_configs = get_entity_field_config('switchboard', db)
    basic_fields = [f for f in field_configs if f.get('category') == 'basic' and f.get('enabled')]
    
    # Get dropdown sources for dropdown-enabled fields
    categories = db.query(DropdownSource.category).distinct().all()
    dropdown_sources = {}
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order).all()
        dropdown_sources[category] = sources
    
    # Legacy: také posílám switchboard_types pro zpětnou kompatibilitu
    switchboard_types = []
    dropdown_config = db.query(DropdownConfig).filter(
        DropdownConfig.entity_type == "switchboard",
        DropdownConfig.field_name == "switchboard_type",
        DropdownConfig.dropdown_enabled == True
    ).first()
    
    if dropdown_config and dropdown_config.dropdown_category:
        dropdown_values = db.query(DropdownSource).filter(
            DropdownSource.category == dropdown_config.dropdown_category
        ).order_by(DropdownSource.display_order).all()
        switchboard_types = [v.value for v in dropdown_values]
    
    return templates.TemplateResponse("modals/quick_entry_step2.html", {
        "request": request,
        "revision_name": revision_name,
        "field_configs": basic_fields,
        "dropdown_sources": dropdown_sources,
        "switchboard_types": switchboard_types  # Legacy
    })


@app.post("/api/quick-entry/complete", response_class=HTMLResponse)
async def quick_entry_complete(
    request: Request,
    db: Session = Depends(get_db),
    switchboards: str = Form(...)
):
    """
    Vytvoří revizi + všechny rozváděče najednou
    Vrátí success screen
    """
    user_id = get_current_user(request)
    temp_revision = request.session.get('temp_revision', {})
    
    if not temp_revision:
        # Pokud nejsou data v session, vrátit error
        return HTMLResponse(
            content="<div class='p-4 text-red-600'>Chyba: Session data nebyla nalezena. Zkuste to znovu.</div>",
            status_code=400
        )
    
    try:
        # Vytvoření revize
        new_revision = Revision(
            user_id=user_id,
            revision_name=temp_revision.get('revision_name'),
            revision_client=temp_revision.get('revision_client'),
            revision_address=temp_revision.get('revision_address'),
            revision_code=temp_revision.get('revision_code'),
            revision_type=temp_revision.get('revision_type'),
            revision_technician=temp_revision.get('revision_technician'),
            revision_description=temp_revision.get('revision_description'),
            revision_date_of_creation=datetime.now().date()
        )
        
        # Parse start_date pokud existuje
        if temp_revision.get('revision_start_date'):
            try:
                new_revision.revision_start_date = datetime.strptime(
                    temp_revision.get('revision_start_date'), 
                    '%Y-%m-%d'
                ).date()
            except:
                pass
        
        db.add(new_revision)
        db.flush()  # Získání revision_id
        
        # Vytvoření rozváděčů
        switchboards_data = json.loads(switchboards)
        for sb_data in switchboards_data:
            new_switchboard = Switchboard(
                revision_id=new_revision.revision_id,
                switchboard_name=sb_data.get('name'),
                switchboard_type=sb_data.get('type') if sb_data.get('type') else None,
                switchboard_order=sb_data.get('order', 0)
            )
            db.add(new_switchboard)
        
        db.commit()
        
        # Vyčištění session
        request.session.pop('temp_revision', None)
        
        return templates.TemplateResponse("modals/quick_entry_success.html", {
            "request": request,
            "revision_id": new_revision.revision_id,
            "revision_name": new_revision.revision_name,
            "switchboards_count": len(switchboards_data)
        })
        
    except Exception as e:
        db.rollback()
        return HTMLResponse(
            content=f"<div class='p-4 text-red-600'>Chyba při vytváření revize: {str(e)}</div>",
            status_code=500
        )


# === ADMIN FORCE SEED ENDPOINT ===
@app.get("/admin/force-seed-field-config")
async def admin_force_seed(db: Session = Depends(get_db)):
    """
    🔧 ADMIN: Force seed field config
    Smaže všechny existující záznamy a vytvoří je znovu
    
    POUŽITÍ:
    1. Otevři: https://your-app.railway.app/admin/force-seed-field-config
    2. Počkej na zprávu "success"
    3. Refresh /settings
    
    ⚠️ POZOR: Toto smaže všechny custom úpravy field configu!
    """
    try:
        # Spusť force seed
        run_field_config_seed(force=True)
        
        # Zkontroluj kolik záznamů je teď v DB
        count = db.query(DropdownConfig).count()
        
        # Zkontroluj kolik je pro revision
        revision_count = db.query(DropdownConfig).filter(
            DropdownConfig.entity_type == 'revision'
        ).count()
        
        return {
            "status": "success",
            "message": "Field config byl úspěšně re-seedován!",
            "total_fields": count,
            "revision_fields": revision_count,
            "next_step": "Otevři /settings a měla by se zobrazit pole!"
        }
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# === TERMINAL DEVICE QUICK ADD ENDPOINTS ===

@app.get("/circuit/{circuit_id}/terminal/list-with-form", response_class=HTMLResponse)
async def terminal_list_with_form(circuit_id: int, request: Request, db: Session = Depends(get_db)):
    """Returns the list of terminal devices + empty form container for HTMX"""
    user_id = get_current_user(request)
    circuit = db.query(Circuit).join(Device).join(Switchboard).join(Revision).filter(
        Circuit.circuit_id == circuit_id, Revision.user_id == user_id
    ).first()
    if not circuit:
        return "<div class='text-red-500 p-4'>Obvod nenalezen</div>"
    dropdown_sources = {}
    categories = db.query(DropdownSource.category).distinct().all()
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(DropdownSource.category == category).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    return templates.TemplateResponse("components/terminal_list_with_form.html", {
        "request": request, "circuit_id": circuit_id, "terminals": circuit.terminal_devices, 
        "dropdown_sources": dropdown_sources, "show_form": False
    })

@app.get("/circuit/{circuit_id}/terminal/quick-add-form", response_class=HTMLResponse)
async def get_terminal_quick_add_form(circuit_id: int, request: Request, db: Session = Depends(get_db)):
    """Returns HTML with inline form for adding terminal device"""
    user_id = get_current_user(request)
    circuit = db.query(Circuit).join(Device).join(Switchboard).join(Revision).filter(
        Circuit.circuit_id == circuit_id, Revision.user_id == user_id
    ).first()
    if not circuit:
        return "<div class='text-red-500 p-4'>Obvod nenalezen</div>"
    dropdown_sources = {}
    categories = db.query(DropdownSource.category).distinct().all()
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(DropdownSource.category == category).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    return templates.TemplateResponse("components/quick_add_terminal_form.html", {
        "request": request, "circuit_id": circuit_id, "dropdown_sources": dropdown_sources
    })

@app.post("/circuit/{circuit_id}/terminal/quick-add", response_class=HTMLResponse)
async def quick_add_terminal(circuit_id: int, request: Request, db: Session = Depends(get_db)):
    """Creates new terminal device and returns updated list"""
    user_id = get_current_user(request)
    circuit = db.query(Circuit).join(Device).join(Switchboard).join(Revision).filter(
        Circuit.circuit_id == circuit_id, Revision.user_id == user_id
    ).first()
    if not circuit:
        return "<div class='text-red-500 p-4'>Obvod nenalezen</div>"
    form_data = await request.form()
    def get_value(key, convert_type=None):
        value = form_data.get(key, "").strip()
        if not value:
            return None
        if convert_type == int:
            return int(value) if value else None
        if convert_type == float:
            return float(value) if value else None
        return value
    order = get_value("terminal_order", int)
    if order is None:
        max_order = db.query(func.max(TerminalDevice.terminal_order)).filter(TerminalDevice.circuit_id == circuit_id).scalar()
        order = (max_order or 0) + 1
    new_terminal = TerminalDevice(
        circuit_id=circuit_id, terminal_name=get_value("terminal_name"), terminal_type=get_value("terminal_type"),
        terminal_order=order, terminal_description=get_value("terminal_description"), 
        terminal_location=get_value("terminal_location"), terminal_power=get_value("terminal_power", float),
        terminal_note=get_value("terminal_note")
    )
    db.add(new_terminal)
    db.commit()
    db.refresh(new_terminal)
    circuit = db.query(Circuit).filter(Circuit.circuit_id == circuit_id).first()
    dropdown_sources = {}
    categories = db.query(DropdownSource.category).distinct().all()
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(DropdownSource.category == category).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    return templates.TemplateResponse("components/terminal_list_with_form.html", {
        "request": request, "circuit_id": circuit_id, "terminals": circuit.terminal_devices,
        "dropdown_sources": dropdown_sources, "show_form": False
    })
