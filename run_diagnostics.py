#!/usr/bin/env python3
"""
🔍 MASTER DIAGNOSTIC SCRIPT
===========================
Spustí všechny diagnostické kontroly najednou
"""

import subprocess
import sys
import os

def run_script(script_name, description):
    print("\n" + "="*80)
    print(f"🚀 Running: {description}")
    print("="*80)
    
    try:
        result = subprocess.run([sys.executable, script_name], 
                              capture_output=False, 
                              text=True,
                              cwd=os.path.dirname(os.path.abspath(__file__)))
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running {script_name}: {e}")
        return False

def main():
    print("\n" + "="*80)
    print("🔍 REVIZE APP - COMPLETE DIAGNOSTIC")
    print("="*80)
    print("""
    Tento script spustí všechny diagnostické kontroly:
    1. Database check - co je skutečně v databázi
    2. Dropdown sources - jaké kategorie a hodnoty existují
    3. Field config test - co vrací get_entity_field_config()
    4. Dropdown visibility check - který pole jsou viditelná
    """)
    
    scripts = [
        ("check_database.py", "Database Check - Raw Data"),
        ("check_dropdown_sources.py", "Dropdown Sources & Categories"),
        ("test_field_config.py", "Field Config Output Test"),
        ("check_dropdowns.py", "Dropdown Visibility Analysis"),
    ]
    
    results = []
    for script, desc in scripts:
        if os.path.exists(script):
            success = run_script(script, desc)
            results.append((script, success))
        else:
            print(f"\n⚠️  Script {script} not found, skipping...")
            results.append((script, False))
    
    print("\n" + "="*80)
    print("📊 DIAGNOSTIC SUMMARY")
    print("="*80 + "\n")
    
    for script, success in results:
        status = "✅" if success else "❌"
        print(f"{status} {script}")
    
    print("\n" + "="*80)
    print("🎯 NEXT STEPS")
    print("="*80 + "\n")
    print("Na základě výsledků diagnostiky:")
    print("1. Pokud jsou pole SKRYTÁ → spusť: python fix_dropdown_visibility.py")
    print("2. Pokud chybí KATEGORIE → přidej je v /settings")
    print("3. Pokud chybí HODNOTY v kategoriích → přidej je v /settings")
    print("4. Restartuj aplikaci a zkontroluj formuláře")
    print()

if __name__ == "__main__":
    main()
