#!/usr/bin/env python3
"""
🔍 DIAGNOSTIKA VIDITELNOSTI POLÍ
=================================
Zkontroluje, která pole jsou enabled/disabled v databázi
a jak to ovlivňuje zobrazení kategorií ve formulářích.
"""

from sqlalchemy.orm import Session
from database import SessionLocal
from models import DropdownConfig
from collections import defaultdict

def check_field_visibility():
    """Zkontroluje viditelnost polí podle kategorií"""
    db = SessionLocal()
    
    try:
        print("\n" + "="*70)
        print("🔍 KONTROLA VIDITELNOSTI POLÍ")
        print("="*70 + "\n")
        
        # Načti všechna pole pro revizi
        all_fields = db.query(DropdownConfig).filter(
            DropdownConfig.entity_type == 'revision'
        ).order_by(DropdownConfig.display_order).all()
        
        # Seskup podle kategorie
        by_category = defaultdict(list)
        for field in all_fields:
            category = field.field_category or 'other'
            by_category[category].append(field)
        
        # Kategorie názvy
        category_names = {
            'basic': '📋 Základní informace',
            'additional': '📝 Dodatečné údaje',
            'technical': '🔧 Technické údaje',
            'administrative': '📄 Administrativní údaje',
            'measurements': '📊 Měření',
            'other': '📦 Ostatní'
        }
        
        # Analyzuj každou kategorii
        print("STAV KATEGORIÍ VE FORMULÁŘI:\n")
        
        for category in ['basic', 'additional', 'technical', 'administrative', 'measurements', 'other']:
            if category not in by_category:
                continue
                
            fields = by_category[category]
            enabled_count = sum(1 for f in fields if f.enabled)
            disabled_count = sum(1 for f in fields if not f.enabled)
            
            # Určí, zda se karta zobrazí
            will_show = enabled_count > 0
            
            status = "✅ ZOBRAZÍ SE" if will_show else "❌ NEZOBRAZÍ SE"
            print(f"{category_names.get(category, category)}")
            print(f"  Status: {status}")
            print(f"  Enabled polí: {enabled_count}/{len(fields)}")
            print(f"  Disabled polí: {disabled_count}/{len(fields)}")
            
            if disabled_count > 0:
                print(f"  \n  Disabled pole:")
                for field in fields:
                    if not field.enabled:
                        print(f"    - {field.field_name} ({field.field_label})")
            
            print()
        
        # Součet
        total = len(all_fields)
        enabled = sum(1 for f in all_fields if f.enabled)
        disabled = sum(1 for f in all_fields if not f.enabled)
        
        print("="*70)
        print(f"CELKOVÝ PŘEHLED:")
        print(f"  Celkem polí: {total}")
        print(f"  Enabled: {enabled} ({enabled/total*100:.1f}%)")
        print(f"  Disabled: {disabled} ({disabled/total*100:.1f}%)")
        print("="*70 + "\n")
        
        # Doporučení
        if disabled > 0:
            print("💡 DOPORUČENÍ:")
            print("  1. Pro zobrazení karet enable pole v Nastavení → Viditelnost polí")
            print("  2. Nebo spusť: python enable_all_fields.py")
            print()
        
    finally:
        db.close()


if __name__ == "__main__":
    check_field_visibility()
