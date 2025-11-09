#!/usr/bin/env python3
"""
🌱 SEED FIELD CONFIG - Inicializace konfigurace polí
====================================================
Tento skript naplní dropdown_config tabulku výchozí konfigurací
pro všech 5 entit v aplikaci.

Použití:
    python seed_field_config.py

Co dělá:
    1. Vytvoří konfiguraci pro všechna pole v každé entitě
    2. Nastaví kategorie (basic, additional, measurements, technical, administrative)
    3. Nastaví viditelnost (enabled/disabled)
    4. Nastaví pořadí zobrazení (display_order)
"""

import os
import sys
from sqlalchemy.orm import Session

# Import database
from database import SessionLocal
from models import DropdownConfig

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

def print_info(text):
    print(f"  {text}")

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


# ============================================================================
# KONFIGURACE POLÍ PRO JEDNOTLIVÉ ENTITY
# ============================================================================

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


def seed_field_config():
    """Naplní dropdown_config výchozí konfigurací"""
    print_header("🌱 SEED FIELD CONFIG")
    
    db = SessionLocal()
    try:
        total_inserted = 0
        total_updated = 0
        total_skipped = 0
        
        for entity_type, fields in FIELD_CONFIGS.items():
            print_info(f"\nProcessing entity: {entity_type}")
            
            for field_name, field_label, category, field_type, enabled, required, display_order in fields:
                # Check if config already exists
                existing = db.query(DropdownConfig).filter(
                    DropdownConfig.entity_type == entity_type,
                    DropdownConfig.field_name == field_name
                ).first()
                
                if existing:
                    # Update existing config
                    existing.field_label = field_label
                    existing.field_category = category
                    existing.field_type = field_type
                    existing.enabled = enabled
                    existing.is_required = required
                    existing.display_order = display_order
                    total_updated += 1
                else:
                    # Create new config
                    config = DropdownConfig(
                        entity_type=entity_type,
                        field_name=field_name,
                        field_label=field_label,
                        field_category=category,
                        field_type=field_type,
                        enabled=enabled,
                        is_required=required,
                        display_order=display_order,
                        dropdown_enabled=False,  # Default: no dropdown
                        dropdown_category=None
                    )
                    db.add(config)
                    total_inserted += 1
            
            db.commit()
            print_success(f"✓ Seeded {entity_type}: {len(fields)} fields")
        
        print_header("✅ SEED DOKONČEN")
        print_success(f"Nově vytvořeno: {total_inserted} konfigurací")
        print_success(f"Aktualizováno: {total_updated} konfigurací")
        print_info(f"\nCelkem: {total_inserted + total_updated} konfigurací polí\n")
        
        return True
        
    except Exception as e:
        print_error(f"Chyba při seed: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def main():
    """Hlavní funkce"""
    print_header("🚀 REVIZE APP - SEED FIELD CONFIG")
    print_info("Inicializace konfigurace polí pro všechny entity\n")
    
    if seed_field_config():
        print_header("✅ SEED ÚSPĚŠNĚ DOKONČEN")
        print_info("Můžeš nyní otevřít /settings a konfigurovat pole!\n")
        return 0
    else:
        print_header("❌ SEED SELHAL")
        return 1


if __name__ == "__main__":
    sys.exit(main())
