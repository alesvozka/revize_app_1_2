#!/usr/bin/env python3
"""
🔄 MIGRACE: Rekategorizace polí pro unified strukturu
=====================================================
Tento script:
1. Přesune pole do správných kategorií
2. Přidá novou kategorii "dates"
3. Zruší kategorii "additional"
4. Enable všechna pole pro zobrazení
"""

import sys
from sqlalchemy.orm import Session
from database import SessionLocal
from models import DropdownConfig, FieldCategory

# Barvy pro výstup
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
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


def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")


def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")


# NOVÁ UNIFIED STRUKTURA
UNIFIED_CATEGORIES = {
    'basic': {
        'fields': [
            'revision_code',
            'revision_name',
            'revision_owner',
            'revision_client',
            'revision_address',
            'revision_type',
            'revision_description',
            'revision_short_description',
        ],
        'label': 'Základní informace',
        'icon': '📋',
        'order': 10
    },
    'dates': {
        'fields': [
            'revision_date_of_creation',
            'revision_start_date',
            'revision_end_date',
            'revision_date_of_previous_revision',
            'revision_recommended_date_for_next_revision',
        ],
        'label': 'Termíny',
        'icon': '📅',
        'order': 20
    },
    'technical': {
        'fields': [
            'revision_measuring_instrument_manufacturer_type',
            'revision_measuring_instrument_serial_number',
            'revision_measuring_instrument_calibration',
            'revision_measuring_instrument_calibration_validity',
            'revision_overall_assessment',
        ],
        'label': 'Technické údaje',
        'icon': '🔧',
        'order': 30
    },
    'administrative': {
        'fields': [
            'revision_technician',
            'revision_certificate_number',
            'revision_authorization_number',
            'revision_contractor',
            'revision_project_documentation',
            'revision_attachment',
            'revision_attachment_submitter',
            'revision_attachment_producer',
            'revision_attachment_date_of_creation',
            'revision_number_of_copies_technician',
            'revision_number_of_copies_owner',
            'revision_number_of_copies_contractor',
            'revision_number_of_copies_client',
        ],
        'label': 'Administrativní údaje',
        'icon': '📄',
        'order': 40
    }
}


def migrate_field_categories(enable_all=True, dry_run=False):
    """
    Migruje pole do nové unified struktury
    
    Args:
        enable_all: pokud True, enable všechna pole
        dry_run: pokud True, pouze simuluje změny bez commitování
    """
    db = SessionLocal()
    
    try:
        print_header("🔄 MIGRACE FIELD CATEGORIES")
        
        if dry_run:
            print_warning("DRY RUN MODE - žádné změny nebudou uloženy")
            print()
        
        # Statistiky
        stats = {
            'moved': 0,
            'enabled': 0,
            'errors': 0,
            'not_found': []
        }
        
        # Pro každou kategorii
        for category_key, category_info in UNIFIED_CATEGORIES.items():
            print_info(f"\n{category_info['icon']} {category_info['label']} ({category_key})")
            print_info("-" * 60)
            
            # Pro každé pole v kategorii
            for field_name in category_info['fields']:
                # Najdi pole v databázi
                field = db.query(DropdownConfig).filter(
                    DropdownConfig.entity_type == 'revision',
                    DropdownConfig.field_name == field_name
                ).first()
                
                if not field:
                    print_error(f"  Pole '{field_name}' nenalezeno v databázi!")
                    stats['not_found'].append(field_name)
                    stats['errors'] += 1
                    continue
                
                # Změna kategorie
                old_category = field.field_category
                if old_category != category_key:
                    print_info(f"  {field_name}: {old_category or 'None'} → {category_key}")
                    field.field_category = category_key
                    stats['moved'] += 1
                else:
                    print_info(f"  {field_name}: ✓ (už v {category_key})")
                
                # Enable pole
                if enable_all and not field.enabled:
                    print_info(f"    → enabling")
                    field.enabled = True
                    stats['enabled'] += 1
        
        # Commit změny
        if not dry_run:
            db.commit()
            print_success(f"\n✅ Změny uloženy do databáze!")
        else:
            db.rollback()
            print_warning(f"\n⚠ Dry run - změny NEBYLY uloženy")
        
        # Výsledky
        print_header("📊 VÝSLEDKY MIGRACE")
        print_success(f"Pole přesunuta do jiných kategorií: {stats['moved']}")
        print_success(f"Pole enabled: {stats['enabled']}")
        
        if stats['not_found']:
            print_error(f"Pole nenalezena: {len(stats['not_found'])}")
            for field_name in stats['not_found']:
                print_info(f"  - {field_name}")
        
        if stats['errors'] > 0:
            print_warning(f"\nCelkem chyb: {stats['errors']}")
            return False
        
        print_header("✅ MIGRACE DOKONČENA")
        
        if not dry_run:
            print_info("Další kroky:")
            print_info("  1. Restartuj aplikaci")
            print_info("  2. Otevři formulář pro vytvoření revize")
            print_info("  3. Měl bys vidět 4 karty:")
            print_info("     - 📋 Základní informace")
            print_info("     - 📅 Termíny")
            print_info("     - 🔧 Technické údaje")
            print_info("     - 📄 Administrativní údaje")
        
        return True
        
    except Exception as e:
        print_error(f"Chyba při migraci: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
        return False
    finally:
        db.close()


def create_field_categories_if_not_exist():
    """Vytvoří field_categories záznamy pro všechny kategorie"""
    db = SessionLocal()
    
    try:
        print_header("📋 KONTROLA FIELD CATEGORIES")
        
        for category_key, category_info in UNIFIED_CATEGORIES.items():
            # Zkontroluj, zda kategorie existuje
            existing = db.query(FieldCategory).filter(
                FieldCategory.entity_type == 'revision',
                FieldCategory.category_key == category_key
            ).first()
            
            if existing:
                print_info(f"✓ Kategorie '{category_key}' už existuje")
            else:
                # Vytvoř novou kategorii
                new_cat = FieldCategory(
                    entity_type='revision',
                    category_key=category_key,
                    category_label=category_info['label'],
                    display_order=category_info['order'],
                    icon=category_info['icon']
                )
                db.add(new_cat)
                print_success(f"+ Vytvořena kategorie '{category_key}': {category_info['label']}")
        
        db.commit()
        print_success("\n✅ Field categories OK!")
        
    except Exception as e:
        print_error(f"Chyba při vytváření kategorií: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def main():
    """Hlavní funkce"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Migrace field categories')
    parser.add_argument('--dry-run', action='store_true', help='Simulovat bez ukládání změn')
    parser.add_argument('--no-enable', action='store_true', help='Neenable pole automaticky')
    
    args = parser.parse_args()
    
    print_header("🚀 UNIFIED CARD STRUCTURE MIGRATION")
    print_info("Tento script přesune pole do nové unified struktury kategorií\n")
    
    # Krok 1: Vytvoř field_categories
    create_field_categories_if_not_exist()
    
    # Krok 2: Migruj pole
    enable_all = not args.no_enable
    success = migrate_field_categories(enable_all=enable_all, dry_run=args.dry_run)
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())
