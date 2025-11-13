#!/usr/bin/env python3
"""
🔧 FIX DROPDOWN VISIBILITY
=========================
Tento script automaticky zapne viditelnost (enabled=True) pro všechna pole,
která mají zapnutý dropdown (dropdown_enabled=True).

Problém: Dropdown je zapnutý, ale pole není viditelné → widget se nezobrazí!
Řešení: Automaticky zapnout viditelnost pro všechna pole s dropdownem.
"""

from database import SessionLocal
from models import DropdownConfig

def fix_dropdown_visibility():
    db = SessionLocal()
    try:
        print("\n" + "="*80)
        print("🔧 FIX DROPDOWN VISIBILITY")
        print("="*80 + "\n")
        
        # Find fields with dropdown enabled but field disabled
        problematic_fields = db.query(DropdownConfig).filter(
            DropdownConfig.dropdown_enabled == True,
            DropdownConfig.enabled == False
        ).all()
        
        if not problematic_fields:
            print("✅ Žádné problémy k opravě!")
            print("   Všechna pole s dropdownem jsou už viditelná.\n")
            return
        
        print(f"⚠️  Nalezeno {len(problematic_fields)} polí s problémem:")
        print("   (dropdown zapnutý, ale pole skryté)\n")
        
        for field in problematic_fields:
            label = field.custom_label or field.field_label or field.field_name
            print(f"  📝 {field.entity_type:15} | {field.field_name:40} | {label}")
        
        print("\n" + "-"*80)
        response = input("\n❓ Chceš automaticky zapnout viditelnost těchto polí? (ano/ne): ")
        
        if response.lower() not in ['ano', 'a', 'yes', 'y']:
            print("\n❌ Oprava zrušena.\n")
            return
        
        # Fix the fields
        fixed_count = 0
        for field in problematic_fields:
            field.enabled = True
            fixed_count += 1
        
        db.commit()
        
        print(f"\n✅ Opraveno {fixed_count} polí!")
        print("   Nyní by se měly dropdowny zobrazovat ve formulářích.\n")
        
        print("="*80)
        print("🎉 HOTOVO!")
        print("="*80 + "\n")
        
    except Exception as e:
        print(f"\n❌ Chyba: {e}\n")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    fix_dropdown_visibility()
