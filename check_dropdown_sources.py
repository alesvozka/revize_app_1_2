#!/usr/bin/env python3
"""
Check dropdown sources - what categories exist and what values they have
"""
import sys
sys.path.insert(0, '/tmp/revize_app_phase5-3')

from database import SessionLocal
from models import DropdownSource, DropdownConfig

def check_dropdown_sources():
    db = SessionLocal()
    try:
        print("\n" + "="*80)
        print("🔍 DROPDOWN SOURCES & CATEGORIES")
        print("="*80 + "\n")
        
        # Get all categories
        categories = db.query(DropdownSource.category).distinct().order_by(DropdownSource.category).all()
        
        print(f"📊 Found {len(categories)} categories in dropdown_sources:\n")
        
        for cat in categories:
            category = cat[0]
            sources = db.query(DropdownSource).filter(
                DropdownSource.category == category
            ).order_by(DropdownSource.display_order, DropdownSource.value).all()
            
            print(f"📁 {category}")
            print(f"   Values: {len(sources)}")
            for source in sources[:5]:  # Show first 5
                print(f"     - {source.value}")
            if len(sources) > 5:
                print(f"     ... and {len(sources) - 5} more")
            print()
        
        # Now check which categories are actually used in dropdown_config
        print("="*80)
        print("🔗 CONFIGURED DROPDOWNS (from dropdown_config)")
        print("="*80 + "\n")
        
        configs_with_dropdown = db.query(DropdownConfig).filter(
            DropdownConfig.dropdown_enabled == True,
            DropdownConfig.dropdown_category != None
        ).all()
        
        print(f"Found {len(configs_with_dropdown)} fields with dropdown enabled:\n")
        
        used_categories = set()
        for config in configs_with_dropdown:
            label = config.custom_label or config.field_label or config.field_name
            category = config.dropdown_category
            used_categories.add(category)
            
            # Check if category exists in dropdown_sources
            sources_count = db.query(DropdownSource).filter(
                DropdownSource.category == category
            ).count()
            
            status = "✅" if sources_count > 0 else "❌ MISSING"
            enabled_status = "✅" if config.enabled else "❌ HIDDEN"
            
            print(f"{config.entity_type:15} | {config.field_name:40} | {label:30}")
            print(f"                  Category: {category:20} | Values: {sources_count:3} {status} | Visible: {enabled_status}")
            print()
        
        # Check for categories used but not existing
        print("="*80)
        print("⚠️  VALIDATION")
        print("="*80 + "\n")
        
        existing_categories = {cat[0] for cat in categories}
        missing = used_categories - existing_categories
        
        if missing:
            print(f"❌ {len(missing)} categories are configured but have NO values:")
            for cat in missing:
                fields = db.query(DropdownConfig).filter(
                    DropdownConfig.dropdown_category == cat
                ).all()
                print(f"   - '{cat}' (used by {len(fields)} field(s))")
                for field in fields:
                    label = field.custom_label or field.field_label
                    print(f"      * {field.entity_type}.{field.field_name} ({label})")
            print()
        else:
            print("✅ All configured categories have values in dropdown_sources\n")
        
    finally:
        db.close()

if __name__ == "__main__":
    check_dropdown_sources()
