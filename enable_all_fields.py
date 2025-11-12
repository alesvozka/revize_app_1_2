#!/usr/bin/env python3
"""
✅ ENABLE VŠECH POLÍ
====================
Nastaví všechna pole entity jako viditelná (enabled=True).
"""

import sys
from sqlalchemy.orm import Session
from database import SessionLocal
from models import DropdownConfig

def enable_all_fields(entity_type='revision', enable_all=True):
    """
    Enable všechna pole pro danou entitu
    
    Args:
        entity_type: typ entity ('revision', 'switchboard', atd.)
        enable_all: True = enable všechna pole, False = jen enable pole podle seznamu
    """
    db = SessionLocal()
    
    try:
        print("\n" + "="*70)
        print(f"✅ ENABLE POLÍ PRO ENTITU: {entity_type.upper()}")
        print("="*70 + "\n")
        
        if enable_all:
            # Enable VŠECHNA pole
            fields = db.query(DropdownConfig).filter(
                DropdownConfig.entity_type == entity_type,
                DropdownConfig.enabled == False
            ).all()
            
            if not fields:
                print("✓ Všechna pole jsou již enabled!")
                return
            
            print(f"Enabling {len(fields)} disabled polí:\n")
            
            for field in fields:
                print(f"  ✓ {field.field_name} ({field.field_label})")
                field.enabled = True
            
            db.commit()
            print(f"\n✅ Všech {len(fields)} polí bylo successfully enabled!")
            
        else:
            # Enable jen důležitá pole (základní, dodatečné, technické, administrativa)
            important_categories = ['basic', 'additional', 'technical', 'administrative']
            
            fields = db.query(DropdownConfig).filter(
                DropdownConfig.entity_type == entity_type,
                DropdownConfig.field_category.in_(important_categories),
                DropdownConfig.enabled == False
            ).all()
            
            if not fields:
                print("✓ Všechna důležitá pole jsou již enabled!")
                return
            
            print(f"Enabling {len(fields)} důležitých polí:\n")
            
            for field in fields:
                print(f"  ✓ {field.field_category}: {field.field_name} ({field.field_label})")
                field.enabled = True
            
            db.commit()
            print(f"\n✅ Všech {len(fields)} důležitých polí bylo successfully enabled!")
        
        print("\n" + "="*70)
        print("DALŠÍ KROKY:")
        print("  1. Restartuj aplikaci")
        print("  2. Otevři formulář pro vytvoření revize")
        print("  3. Měl bys vidět všechny karty kategorií!")
        print("="*70 + "\n")
        
    except Exception as e:
        print(f"❌ CHYBA: {e}")
        db.rollback()
        import traceback
        traceback.print_exc()
    finally:
        db.close()


def main():
    """Hlavní funkce"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enable pole pro entity')
    parser.add_argument('--entity', default='revision', help='Typ entity (default: revision)')
    parser.add_argument('--all', action='store_true', help='Enable VŠECHNA pole (default: jen důležité)')
    parser.add_argument('--important-only', action='store_true', help='Enable jen důležité kategorie')
    
    args = parser.parse_args()
    
    if args.all:
        enable_all_fields(args.entity, enable_all=True)
    elif args.important_only:
        enable_all_fields(args.entity, enable_all=False)
    else:
        # Default: enable všechna pole
        enable_all_fields(args.entity, enable_all=True)


if __name__ == "__main__":
    main()
