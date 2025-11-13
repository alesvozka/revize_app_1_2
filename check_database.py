#!/usr/bin/env python3
"""
Simple SQL check - what's actually in the database
"""
import sys
sys.path.insert(0, '/tmp/revize_app_phase5-3')

from database import SessionLocal
from models import DropdownConfig

def check_database():
    db = SessionLocal()
    try:
        print("\n" + "="*80)
        print("🔍 DATABASE CHECK - DropdownConfig Table")
        print("="*80 + "\n")
        
        # Get specific fields that should have dropdowns based on screenshots
        test_fields = [
            ('revision', 'revision_type'),
            ('revision', 'revision_client'),
            ('revision', 'revision_overall_assessment'),
        ]
        
        for entity, field_name in test_fields:
            print(f"\n📋 Checking: {entity}.{field_name}")
            print("-" * 60)
            
            config = db.query(DropdownConfig).filter(
                DropdownConfig.entity_type == entity,
                DropdownConfig.field_name == field_name
            ).first()
            
            if not config:
                print("  ❌ NOT FOUND in database!")
                continue
            
            print(f"  ID: {config.id}")
            print(f"  Field label: {config.field_label}")
            print(f"  Custom label: {config.custom_label}")
            print(f"  Field category: {config.field_category}")
            print(f"  Display order: {config.display_order}")
            print(f"  ")
            print(f"  ✅ ENABLED (visible): {config.enabled}")
            print(f"  🔽 DROPDOWN ENABLED: {config.dropdown_enabled}")
            print(f"  📁 DROPDOWN CATEGORY: {repr(config.dropdown_category)}")
            print(f"  ")
            
            # Check what the condition would evaluate to
            would_show = config.dropdown_enabled and config.dropdown_category
            print(f"  Would show dropdown widget: {would_show}")
            
            if config.enabled and config.dropdown_enabled and config.dropdown_category:
                print(f"  ✅ THIS SHOULD SHOW DROPDOWN!")
            elif not config.enabled:
                print(f"  ❌ PROBLEM: Field is HIDDEN (enabled=False)")
            elif not config.dropdown_enabled:
                print(f"  ❌ PROBLEM: Dropdown is DISABLED")
            elif not config.dropdown_category:
                print(f"  ❌ PROBLEM: No category selected (dropdown_category is None or empty)")
        
        print("\n" + "="*80)
        print("📊 SUMMARY OF ALL DROPDOWN-ENABLED FIELDS")
        print("="*80 + "\n")
        
        all_dropdowns = db.query(DropdownConfig).filter(
            DropdownConfig.dropdown_enabled == True
        ).order_by(DropdownConfig.entity_type, DropdownConfig.display_order).all()
        
        print(f"Total fields with dropdown_enabled=True: {len(all_dropdowns)}\n")
        
        for config in all_dropdowns:
            label = config.custom_label or config.field_label or config.field_name
            vis = "✅" if config.enabled else "❌"
            cat = config.dropdown_category or "(NONE)"
            print(f"{vis} {config.entity_type:12} | {config.field_name:40} | cat: {cat}")
        
        print()
        
    finally:
        db.close()

if __name__ == "__main__":
    check_database()
