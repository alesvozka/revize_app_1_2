"""
PHASE 4 SEED DATA: Initialize field configuration for all entities
"""
from sqlalchemy.orm import Session
from database import SessionLocal, engine
from models import DropdownConfig

def get_all_field_configurations():
    """
    Returns complete field configuration for all entities
    Format: entity_type -> field_name -> configuration dict
    """
    return {
        "revision": {
            # BASIC FIELDS (cannot be disabled)
            "revision_name": {
                "label": "Název revize",
                "category": "basic",
                "order": 1,
                "enabled": True,
                "required": True,
                "type": "text"
            },
            "revision_client": {
                "label": "Klient",
                "category": "basic",
                "order": 2,
                "enabled": True,
                "required": True,
                "type": "text"
            },
            
            # ADDITIONAL FIELDS (can be disabled)
            "revision_code": {
                "label": "Kód revize",
                "category": "additional",
                "order": 10,
                "enabled": True,
                "required": False,
                "type": "text"
            },
            "revision_owner": {
                "label": "Vlastník",
                "category": "additional",
                "order": 11,
                "enabled": True,
                "required": False,
                "type": "text"
            },
            "revision_address": {
                "label": "Adresa",
                "category": "additional",
                "order": 12,
                "enabled": True,
                "required": False,
                "type": "textarea"
            },
            "revision_description": {
                "label": "Popis",
                "category": "additional",
                "order": 13,
                "enabled": True,
                "required": False,
                "type": "textarea"
            },
            "revision_type": {
                "label": "Typ revize",
                "category": "additional",
                "order": 14,
                "enabled": True,
                "required": False,
                "type": "text"
            },
            "revision_date_of_previous_revision": {
                "label": "Datum předchozí revize",
                "category": "additional",
                "order": 15,
                "enabled": False,
                "required": False,
                "type": "date"
            },
            "revision_start_date": {
                "label": "Datum zahájení",
                "category": "additional",
                "order": 16,
                "enabled": True,
                "required": False,
                "type": "date"
            },
            "revision_end_date": {
                "label": "Datum ukončení",
                "category": "additional",
                "order": 17,
                "enabled": False,
                "required": False,
                "type": "date"
            },
            "revision_date_of_creation": {
                "label": "Datum vytvoření",
                "category": "additional",
                "order": 18,
                "enabled": True,
                "required": False,
                "type": "date"
            },
            "revision_recommended_date_for_next_revision": {
                "label": "Doporučený termín další revize",
                "category": "additional",
                "order": 19,
                "enabled": False,
                "required": False,
                "type": "date"
            },
            "revision_number_of_copies_technician": {
                "label": "Počet vyhotovení - technik",
                "category": "additional",
                "order": 20,
                "enabled": False,
                "required": False,
                "type": "number"
            },
            "revision_number_of_copies_owner": {
                "label": "Počet vyhotovení - vlastník",
                "category": "additional",
                "order": 21,
                "enabled": False,
                "required": False,
                "type": "number"
            },
            "revision_number_of_copies_contractor": {
                "label": "Počet vyhotovení - dodavatel",
                "category": "additional",
                "order": 22,
                "enabled": False,
                "required": False,
                "type": "number"
            },
            "revision_number_of_copies_client": {
                "label": "Počet vyhotovení - klient",
                "category": "additional",
                "order": 23,
                "enabled": False,
                "required": False,
                "type": "number"
            },
            "revision_attachment": {
                "label": "Příloha",
                "category": "additional",
                "order": 24,
                "enabled": False,
                "required": False,
                "type": "text"
            },
            "revision_attachment_submitter": {
                "label": "Předkladatel přílohy",
                "category": "additional",
                "order": 25,
                "enabled": False,
                "required": False,
                "type": "text"
            },
            "revision_attachment_producer": {
                "label": "Zpracovatel přílohy",
                "category": "additional",
                "order": 26,
                "enabled": False,
                "required": False,
                "type": "text"
            },
            "revision_attachment_date_of_creation": {
                "label": "Datum vytvoření přílohy",
                "category": "additional",
                "order": 27,
                "enabled": False,
                "required": False,
                "type": "date"
            },
            "revision_technician": {
                "label": "Revizní technik",
                "category": "additional",
                "order": 28,
                "enabled": True,
                "required": False,
                "type": "text"
            },
            "revision_certificate_number": {
                "label": "Číslo osvědčení",
                "category": "additional",
                "order": 29,
                "enabled": False,
                "required": False,
                "type": "text"
            },
            "revision_authorization_number": {
                "label": "Číslo autorizace",
                "category": "additional",
                "order": 30,
                "enabled": False,
                "required": False,
                "type": "text"
            },
            "revision_project_documentation": {
                "label": "Projektová dokumentace",
                "category": "additional",
                "order": 31,
                "enabled": False,
                "required": False,
                "type": "textarea"
            },
            "revision_contractor": {
                "label": "Dodavatel",
                "category": "additional",
                "order": 32,
                "enabled": False,
                "required": False,
                "type": "text"
            },
            "revision_short_description": {
                "label": "Krátký popis",
                "category": "additional",
                "order": 33,
                "enabled": False,
                "required": False,
                "type": "textarea"
            },
            "revision_measuring_instrument_manufacturer_type": {
                "label": "Měřící přístroj - výrobce/typ",
                "category": "additional",
                "order": 34,
                "enabled": False,
                "required": False,
                "type": "text"
            },
            "revision_measuring_instrument_serial_number": {
                "label": "Měřící přístroj - výrobní číslo",
                "category": "additional",
                "order": 35,
                "enabled": False,
                "required": False,
                "type": "text"
            },
            "revision_measuring_instrument_calibration": {
                "label": "Měřící přístroj - kalibrace",
                "category": "additional",
                "order": 36,
                "enabled": False,
                "required": False,
                "type": "text"
            },
            "revision_measuring_instrument_calibration_validity": {
                "label": "Měřící přístroj - platnost kalibrace",
                "category": "additional",
                "order": 37,
                "enabled": False,
                "required": False,
                "type": "date"
            },
            "revision_overall_assessment": {
                "label": "Celkové hodnocení",
                "category": "additional",
                "order": 38,
                "enabled": False,
                "required": False,
                "type": "textarea"
            },
        },
        
        "switchboard": {
            # BASIC FIELDS
            "switchboard_name": {
                "label": "Název rozváděče",
                "category": "basic",
                "order": 1,
                "enabled": True,
                "required": True,
                "type": "text"
            },
            "switchboard_location": {
                "label": "Umístění",
                "category": "basic",
                "order": 2,
                "enabled": True,
                "required": False,
                "type": "text"
            },
            
            # ADDITIONAL FIELDS
            "switchboard_description": {
                "label": "Popis",
                "category": "additional",
                "order": 10,
                "enabled": True,
                "required": False,
                "type": "textarea"
            },
            "switchboard_type": {
                "label": "Typ rozváděče",
                "category": "additional",
                "order": 11,
                "enabled": True,
                "required": False,
                "type": "text"
            },
            "switchboard_serial_number": {
                "label": "Výrobní číslo",
                "category": "additional",
                "order": 12,
                "enabled": False,
                "required": False,
                "type": "text"
            },
            "switchboard_production_date": {
                "label": "Datum výroby",
                "category": "additional",
                "order": 13,
                "enabled": False,
                "required": False,
                "type": "date"
            },
            "switchboard_ip_rating": {
                "label": "Stupeň krytí (IP)",
                "category": "additional",
                "order": 14,
                "enabled": True,
                "required": False,
                "type": "text"
            },
            "switchboard_impact_protection": {
                "label": "Mechanická odolnost (IK)",
                "category": "additional",
                "order": 15,
                "enabled": False,
                "required": False,
                "type": "text"
            },
            "switchboard_protection_class": {
                "label": "Třída ochrany",
                "category": "additional",
                "order": 16,
                "enabled": False,
                "required": False,
                "type": "text"
            },
            "switchboard_rated_current": {
                "label": "Jmenovitý proud (A)",
                "category": "additional",
                "order": 17,
                "enabled": False,
                "required": False,
                "type": "number"
            },
            "switchboard_rated_voltage": {
                "label": "Jmenovité napětí (V)",
                "category": "additional",
                "order": 18,
                "enabled": False,
                "required": False,
                "type": "number"
            },
            "switchboard_manufacturer": {
                "label": "Výrobce rozváděče",
                "category": "additional",
                "order": 19,
                "enabled": True,
                "required": False,
                "type": "text"
            },
            "switchboard_manufacturer_address": {
                "label": "Adresa výrobce",
                "category": "additional",
                "order": 20,
                "enabled": False,
                "required": False,
                "type": "textarea"
            },
            "switchboard_standards": {
                "label": "Normy",
                "category": "additional",
                "order": 21,
                "enabled": False,
                "required": False,
                "type": "textarea"
            },
            "switchboard_enclosure_type": {
                "label": "Typ skříně",
                "category": "additional",
                "order": 22,
                "enabled": False,
                "required": False,
                "type": "text"
            },
            "switchboard_enclosure_manufacturer": {
                "label": "Výrobce skříně",
                "category": "additional",
                "order": 23,
                "enabled": False,
                "required": False,
                "type": "text"
            },
            "switchboard_enclosure_installation_method": {
                "label": "Způsob instalace skříně",
                "category": "additional",
                "order": 24,
                "enabled": False,
                "required": False,
                "type": "text"
            },
            "switchboard_superior_switchboard": {
                "label": "Nadřazený rozváděč",
                "category": "additional",
                "order": 25,
                "enabled": False,
                "required": False,
                "type": "text"
            },
            "switchboard_superior_circuit_breaker_rated_current": {
                "label": "Nadřazený jistič - proud (A)",
                "category": "additional",
                "order": 26,
                "enabled": False,
                "required": False,
                "type": "number"
            },
            "switchboard_superior_circuit_breaker_trip_characteristic": {
                "label": "Nadřazený jistič - charakteristika",
                "category": "additional",
                "order": 27,
                "enabled": False,
                "required": False,
                "type": "text"
            },
            "switchboard_superior_circuit_breaker_manufacturer": {
                "label": "Nadřazený jistič - výrobce",
                "category": "additional",
                "order": 28,
                "enabled": False,
                "required": False,
                "type": "text"
            },
            "switchboard_superior_circuit_breaker_model": {
                "label": "Nadřazený jistič - model",
                "category": "additional",
                "order": 29,
                "enabled": False,
                "required": False,
                "type": "text"
            },
            "switchboard_main_switch": {
                "label": "Hlavní vypínač",
                "category": "additional",
                "order": 30,
                "enabled": False,
                "required": False,
                "type": "text"
            },
            "switchboard_note": {
                "label": "Poznámka",
                "category": "additional",
                "order": 31,
                "enabled": True,
                "required": False,
                "type": "textarea"
            },
            "switchboard_cable": {
                "label": "Typ kabelu",
                "category": "additional",
                "order": 32,
                "enabled": False,
                "required": False,
                "type": "text"
            },
            "switchboard_cable_installation_method": {
                "label": "Způsob uložení kabelu",
                "category": "additional",
                "order": 33,
                "enabled": False,
                "required": False,
                "type": "text"
            },
        },
        
        "device": {
            # BASIC FIELDS
            "switchboard_device_position": {
                "label": "Pozice",
                "category": "basic",
                "order": 1,
                "enabled": True,
                "required": True,
                "type": "text"
            },
            "switchboard_device_type": {
                "label": "Typ přístroje",
                "category": "basic",
                "order": 2,
                "enabled": True,
                "required": True,
                "type": "text"
            },
            "switchboard_device_rated_current": {
                "label": "Jmenovitý proud (A)",
                "category": "basic",
                "order": 3,
                "enabled": True,
                "required": False,
                "type": "number"
            },
            
            # ADDITIONAL FIELDS
            "switchboard_device_manufacturer": {
                "label": "Výrobce",
                "category": "additional",
                "order": 10,
                "enabled": True,
                "required": False,
                "type": "text"
            },
            "switchboard_device_model": {
                "label": "Model",
                "category": "additional",
                "order": 11,
                "enabled": False,
                "required": False,
                "type": "text"
            },
            "switchboard_device_trip_characteristic": {
                "label": "Vypínací charakteristika",
                "category": "additional",
                "order": 12,
                "enabled": True,
                "required": False,
                "type": "text"
            },
            "switchboard_device_residual_current_ma": {
                "label": "Diferenciální proud (mA)",
                "category": "additional",
                "order": 13,
                "enabled": True,
                "required": False,
                "type": "number"
            },
            "switchboard_device_sub_devices": {
                "label": "Podřízené přístroje",
                "category": "additional",
                "order": 14,
                "enabled": False,
                "required": False,
                "type": "textarea"
            },
            "switchboard_device_poles": {
                "label": "Počet pólů",
                "category": "additional",
                "order": 15,
                "enabled": False,
                "required": False,
                "type": "number"
            },
            "switchboard_device_module_width": {
                "label": "Šířka modulu",
                "category": "additional",
                "order": 16,
                "enabled": False,
                "required": False,
                "type": "number"
            },
        },
        
        "circuit": {
            # BASIC FIELDS
            "circuit_number": {
                "label": "Číslo obvodu",
                "category": "basic",
                "order": 1,
                "enabled": True,
                "required": True,
                "type": "text"
            },
            "circuit_room": {
                "label": "Místnost",
                "category": "basic",
                "order": 2,
                "enabled": True,
                "required": False,
                "type": "text"
            },
            
            # ADDITIONAL FIELDS
            "circuit_description": {
                "label": "Popis",
                "category": "additional",
                "order": 10,
                "enabled": True,
                "required": False,
                "type": "textarea"
            },
            "circuit_description_from_switchboard": {
                "label": "Popis z rozváděče",
                "category": "additional",
                "order": 11,
                "enabled": False,
                "required": False,
                "type": "textarea"
            },
            "circuit_number_of_outlets": {
                "label": "Počet zásuvek",
                "category": "additional",
                "order": 12,
                "enabled": False,
                "required": False,
                "type": "number"
            },
            "circuit_cable_termination": {
                "label": "Ukončení kabelu",
                "category": "additional",
                "order": 13,
                "enabled": False,
                "required": False,
                "type": "text"
            },
            "circuit_cable": {
                "label": "Typ kabelu",
                "category": "additional",
                "order": 14,
                "enabled": True,
                "required": False,
                "type": "text"
            },
            "circuit_cable_installation_method": {
                "label": "Způsob uložení kabelu",
                "category": "additional",
                "order": 15,
                "enabled": False,
                "required": False,
                "type": "text"
            },
        },
        
        "terminal_device": {
            # BASIC FIELDS
            "terminal_device_type": {
                "label": "Typ koncového zařízení",
                "category": "basic",
                "order": 1,
                "enabled": True,
                "required": True,
                "type": "text"
            },
            "terminal_device_marking": {
                "label": "Označení",
                "category": "basic",
                "order": 2,
                "enabled": True,
                "required": False,
                "type": "text"
            },
            
            # ADDITIONAL FIELDS
            "terminal_device_manufacturer": {
                "label": "Výrobce",
                "category": "additional",
                "order": 10,
                "enabled": True,
                "required": False,
                "type": "text"
            },
            "terminal_device_model": {
                "label": "Model",
                "category": "additional",
                "order": 11,
                "enabled": False,
                "required": False,
                "type": "text"
            },
            "terminal_device_power": {
                "label": "Výkon (W)",
                "category": "additional",
                "order": 12,
                "enabled": False,
                "required": False,
                "type": "number"
            },
            "terminal_device_ip_rating": {
                "label": "Stupeň krytí (IP)",
                "category": "additional",
                "order": 13,
                "enabled": False,
                "required": False,
                "type": "text"
            },
            "terminal_device_protection_class": {
                "label": "Třída ochrany",
                "category": "additional",
                "order": 14,
                "enabled": False,
                "required": False,
                "type": "text"
            },
            "terminal_device_serial_number": {
                "label": "Výrobní číslo",
                "category": "additional",
                "order": 15,
                "enabled": False,
                "required": False,
                "type": "text"
            },
            "terminal_device_supply_type": {
                "label": "Typ napájení",
                "category": "additional",
                "order": 16,
                "enabled": False,
                "required": False,
                "type": "text"
            },
            "terminal_device_installation_method": {
                "label": "Způsob instalace",
                "category": "additional",
                "order": 17,
                "enabled": False,
                "required": False,
                "type": "text"
            },
        },
    }


def seed_field_configurations(db: Session):
    """Initialize or update field configurations in database"""
    
    field_configs = get_all_field_configurations()
    
    total_added = 0
    total_updated = 0
    
    for entity_type, fields in field_configs.items():
        print(f"\n📋 Processing entity: {entity_type}")
        
        for field_name, config in fields.items():
            # Check if config already exists
            existing = db.query(DropdownConfig).filter(
                DropdownConfig.entity_type == entity_type,
                DropdownConfig.field_name == field_name
            ).first()
            
            if existing:
                # Update existing config
                existing.field_label = config["label"]
                existing.field_category = config["category"]
                existing.display_order = config["order"]
                existing.enabled = config["enabled"]
                existing.is_required = config["required"]
                existing.field_type = config["type"]
                total_updated += 1
                print(f"   ↻ Updated: {field_name}")
            else:
                # Create new config
                new_config = DropdownConfig(
                    entity_type=entity_type,
                    field_name=field_name,
                    field_label=config["label"],
                    field_category=config["category"],
                    display_order=config["order"],
                    enabled=config["enabled"],
                    is_required=config["required"],
                    field_type=config["type"],
                    dropdown_enabled=False,  # Will be configured separately
                    dropdown_category=None
                )
                db.add(new_config)
                total_added += 1
                print(f"   ✓ Added: {field_name}")
    
    db.commit()
    
    print(f"\n✓ Field configurations seeded!")
    print(f"  Added: {total_added}")
    print(f"  Updated: {total_updated}")


if __name__ == "__main__":
    db = SessionLocal()
    try:
        seed_field_configurations(db)
    finally:
        db.close()
