"""
Startup & migration utilities for Revize App.

Odděleno z main.py kvůli přehlednosti – zde jsou funkce, které se spouští
při startu aplikace (migrace, seed, opravy).
"""

from database import engine, get_db, Base
from models import User, Switchboard, DropdownConfig, FieldCategory, DropdownSource


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

# Custom Jinja2 filter for sorting with None values
