#!/usr/bin/env python3
"""
🧪 TEST: Ověření form_field_dynamic.html makra
===============================================
Tento script ověří, že:
1. Soubor form_field_dynamic.html existuje
2. Obsahuje všechna potřebná makra
3. Makra mají správnou strukturu
"""

import os
import sys
from pathlib import Path

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

def print_error(text):
    print(f"{Colors.RED}✗ {text}{Colors.RESET}")

def print_warning(text):
    print(f"{Colors.YELLOW}⚠ {text}{Colors.RESET}")

def print_info(text):
    print(f"  {text}")


def test_macro_file():
    """Test 1: Existuje soubor?"""
    print_header("TEST 1: Existence souboru")
    
    file_path = Path("templates/components/form_field_dynamic.html")
    
    if file_path.exists():
        print_success(f"Soubor existuje: {file_path}")
        return True, file_path
    else:
        print_error(f"Soubor NEEXISTUJE: {file_path}")
        print_info("Očekávaná cesta: templates/components/form_field_dynamic.html")
        return False, None


def test_macro_content(file_path):
    """Test 2: Obsahuje potřebná makra?"""
    print_header("TEST 2: Obsah maker")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    required_macros = [
        ('render_dynamic_field', 'Makro pro vykreslení jednoho pole'),
        ('render_entity_form', 'Makro pro celý formulář'),
        ('render_field_card_edit', 'Makro pro edit karty')
    ]
    
    all_ok = True
    for macro_name, description in required_macros:
        if f"macro {macro_name}" in content:
            print_success(f"Makro '{macro_name}' nalezeno")
            print_info(f"   → {description}")
        else:
            print_error(f"Makro '{macro_name}' CHYBÍ!")
            print_info(f"   → {description}")
            all_ok = False
    
    return all_ok


def test_macro_features(file_path):
    """Test 3: Obsahuje klíčové funkce?"""
    print_header("TEST 3: Klíčové funkce")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    features = [
        ('dropdown-wrapper', 'Dropdown widgety'),
        ('__ADD_NEW__', 'Přidání nové hodnoty'),
        ('__FREE_TEXT__', 'Volný text'),
        ('handleDropdownChange', 'JavaScript handler'),
        ('field.has_dropdown', 'Kontrola dropdown polí'),
        ('field.category', 'Kategorizace polí'),
        ('field.required', 'Povinná pole'),
        ('dropdown_sources', 'Zdroje dropdown hodnot')
    ]
    
    all_ok = True
    for feature, description in features:
        if feature in content:
            print_success(f"Funkce '{feature}' implementována")
            print_info(f"   → {description}")
        else:
            print_error(f"Funkce '{feature}' CHYBÍ!")
            print_info(f"   → {description}")
            all_ok = False
    
    return all_ok


def test_templates_using_macro():
    """Test 4: Které templates používají makro?"""
    print_header("TEST 4: Templates používající makro")
    
    templates_dir = Path("templates")
    using_macro = []
    
    # Hledáme soubory, které importují z form_field_dynamic.html
    for template_file in templates_dir.rglob("*.html"):
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'form_field_dynamic.html' in content:
                    using_macro.append(template_file)
        except Exception as e:
            pass
    
    if using_macro:
        print_success(f"Nalezeno {len(using_macro)} templates používajících makro:")
        for template in using_macro:
            print_info(f"   → {template}")
    else:
        print_warning("Žádné templates zatím makro nepoužívají")
        print_info("To je OK, pokud je to první implementace")
    
    return True


def test_field_configs_in_db():
    """Test 5: Existují field_configs v databázi?"""
    print_header("TEST 5: Konfigurace polí v databázi")
    
    try:
        from database import SessionLocal
        from models import DropdownConfig, FieldCategory
        
        db = SessionLocal()
        
        # Kontrola DropdownConfig
        field_count = db.query(DropdownConfig).count()
        if field_count > 0:
            print_success(f"DropdownConfig: {field_count} konfigurací polí")
            
            # Kontrola kategorií
            categories = db.query(DropdownConfig.field_category).distinct().all()
            cat_list = [c[0] for c in categories if c[0]]
            if cat_list:
                print_info(f"   Kategorie polí: {', '.join(cat_list)}")
            else:
                print_warning("   Žádné kategorie polí nenalezeny")
        else:
            print_error("DropdownConfig je PRÁZDNÁ!")
            print_info("   Spusť: python seed_field_config.py")
        
        # Kontrola FieldCategory
        cat_count = db.query(FieldCategory).count()
        if cat_count > 0:
            print_success(f"FieldCategory: {cat_count} definic kategorií")
            
            # Ukázka kategorií pro revision
            revision_cats = db.query(FieldCategory).filter(
                FieldCategory.entity_type == 'revision'
            ).order_by(FieldCategory.display_order).all()
            
            if revision_cats:
                print_info("   Kategorie pro Revision:")
                for cat in revision_cats:
                    print_info(f"      • {cat.category_label} ({cat.category_key})")
            else:
                print_warning("   Žádné kategorie pro Revision")
        else:
            print_warning("FieldCategory je prázdná")
            print_info("   Kategorie se seedují automaticky při startu aplikace")
        
        db.close()
        return True
        
    except ImportError:
        print_error("Nelze importovat models/database")
        print_info("   Ujisti se, že jsi ve správné složce projektu")
        return False
    except Exception as e:
        print_error(f"Chyba při čtení DB: {e}")
        return False


def main():
    """Hlavní test funkce"""
    print(f"\n{Colors.BOLD}🧪 TEST: form_field_dynamic.html{Colors.RESET}")
    
    results = []
    
    # Test 1: Existence souboru
    exists, file_path = test_macro_file()
    results.append(("Existence souboru", exists))
    
    if not exists:
        print_header("VÝSLEDEK")
        print_error("Test selhal: Soubor neexistuje!")
        print_info("\nVytvořte soubor pomocí:")
        print_info("  templates/components/form_field_dynamic.html")
        sys.exit(1)
    
    # Test 2: Obsah maker
    macros_ok = test_macro_content(file_path)
    results.append(("Obsah maker", macros_ok))
    
    # Test 3: Klíčové funkce
    features_ok = test_macro_features(file_path)
    results.append(("Klíčové funkce", features_ok))
    
    # Test 4: Templates používající makro
    templates_ok = test_templates_using_macro()
    results.append(("Templates", templates_ok))
    
    # Test 5: Field configs v DB
    db_ok = test_field_configs_in_db()
    results.append(("Databáze", db_ok))
    
    # Celkový výsledek
    print_header("VÝSLEDEK")
    
    all_passed = all(result for _, result in results)
    
    print("\nSouhrn testů:")
    for test_name, result in results:
        if result:
            print_success(f"{test_name}")
        else:
            print_error(f"{test_name}")
    
    if all_passed:
        print(f"\n{Colors.GREEN}{Colors.BOLD}✅ VŠECHNY TESTY PROŠLY!{Colors.RESET}\n")
        print(f"{Colors.BOLD}📋 DALŠÍ KROKY:{Colors.RESET}")
        print("1. Restartuj aplikaci: uvicorn main:app --reload")
        print("2. Otevři formulář: http://localhost:8000/revision/create")
        print("3. Měly by se zobrazit všechny kategorie polí")
        print("4. Zkontroluj, že dropdowny fungují")
        print("\n📖 Pro více info viz: DIAGNOSTIKA_FORMULARE.md\n")
        sys.exit(0)
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}❌ NĚKTERÉ TESTY SELHALY!{Colors.RESET}\n")
        print(f"{Colors.BOLD}🔧 CO DĚLAT:{Colors.RESET}")
        print("1. Zkontroluj chybové zprávy výše")
        print("2. Oprav chybějící části")
        print("3. Spusť test znovu: python test_form_macros.py")
        print("\n📖 Pro více info viz: DIAGNOSTIKA_FORMULARE.md\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
