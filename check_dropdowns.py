#!/usr/bin/env python3
"""
Diagnostic script to check dropdown configuration
"""

from database import SessionLocal
from models import DropdownConfig

def check_dropdowns():
    db = SessionLocal()
    try:
        print("\n" + "="*80)
        print("🔍 DIAGNOSTIKA DROPDOWN KONFIGURACE")
        print("="*80 + "\n")
        
        entities = ['revision', 'switchboard', 'device', 'circuit', 'terminal_device']
        
        for entity in entities:
            print(f"\n📋 {entity.upper()}")
            print("-" * 80)
            
            # Get all configs for this entity
            configs = db.query(DropdownConfig).filter(
                DropdownConfig.entity_type == entity
            ).order_by(DropdownConfig.display_order).all()
            
            if not configs:
                print("  ⚠️  Žádná konfigurace!")
                continue
            
            visible_count = 0
            dropdown_count = 0
            dropdown_with_category = 0
            
            for config in configs:
                status_parts = []
                
                # Check visibility
                if config.enabled:
                    status_parts.append("✅ Viditelné")
                    visible_count += 1
                else:
                    status_parts.append("❌ Skryté")
                
                # Check dropdown
                if config.dropdown_enabled:
                    dropdown_count += 1
                    if config.dropdown_category:
                        status_parts.append(f"🔽 Dropdown: {config.dropdown_category}")
                        dropdown_with_category += 1
                    else:
                        status_parts.append("⚠️  Dropdown BEZ kategorie!")
                else:
                    status_parts.append("📝 Běžný input")
                
                label = config.custom_label or config.field_label or config.field_name
                
                # Only show fields that have dropdowns enabled or are visible
                if config.dropdown_enabled or config.enabled:
                    print(f"  {label:40} | {' | '.join(status_parts)}")
            
            print(f"\n  📊 Souhrn: {visible_count} viditelných polí, "
                  f"{dropdown_count} s dropdown, "
                  f"{dropdown_with_category} s kategorií")
        
        print("\n" + "="*80)
        print("🎯 KONTROLA PROBLÉMŮ")
        print("="*80 + "\n")
        
        # Find problematic configs
        problems = []
        
        # Problem 1: Dropdown enabled but field disabled (not visible)
        invisible_dropdowns = db.query(DropdownConfig).filter(
            DropdownConfig.dropdown_enabled == True,
            DropdownConfig.enabled == False
        ).all()
        
        if invisible_dropdowns:
            problems.append(f"⚠️  {len(invisible_dropdowns)} polí má zapnutý dropdown, ale pole NENÍ VIDITELNÉ!")
            for config in invisible_dropdowns:
                label = config.custom_label or config.field_label or config.field_name
                problems.append(f"    - {config.entity_type}.{config.field_name} ({label})")
        
        # Problem 2: Dropdown enabled but no category
        no_category = db.query(DropdownConfig).filter(
            DropdownConfig.dropdown_enabled == True,
            DropdownConfig.dropdown_category == None
        ).all()
        
        if no_category:
            problems.append(f"⚠️  {len(no_category)} polí má zapnutý dropdown, ale CHYBÍ KATEGORIE!")
            for config in no_category:
                label = config.custom_label or config.field_label or config.field_name
                problems.append(f"    - {config.entity_type}.{config.field_name} ({label})")
        
        # Problem 3: Both problems combined
        both_problems = db.query(DropdownConfig).filter(
            DropdownConfig.dropdown_enabled == True,
            DropdownConfig.enabled == False,
            DropdownConfig.dropdown_category == None
        ).all()
        
        if both_problems:
            problems.append(f"🚨 {len(both_problems)} polí má OBOJÍ problém (skryté + bez kategorie)!")
        
        if problems:
            for problem in problems:
                print(problem)
        else:
            print("✅ Žádné problémy nenalezeny!")
        
        print("\n" + "="*80 + "\n")
        
    finally:
        db.close()

if __name__ == "__main__":
    check_dropdowns()
