#!/usr/bin/env python3
"""
Test script to check what get_entity_field_config returns
"""
import sys
sys.path.insert(0, '/tmp/revize_app_phase5-3')

from database import SessionLocal
from models import DropdownConfig

def test_field_config():
    db = SessionLocal()
    try:
        print("\n" + "="*80)
        print("🔍 TEST get_entity_field_config OUTPUT")
        print("="*80 + "\n")
        
        # Simulate what get_entity_field_config does
        entity_type = 'revision'
        
        fields = db.query(DropdownConfig).filter(
            DropdownConfig.entity_type == entity_type,
            DropdownConfig.enabled == True
        ).order_by(DropdownConfig.display_order).all()
        
        print(f"📋 Entity: {entity_type}")
        print(f"📊 Found {len(fields)} enabled fields\n")
        
        result = []
        for field in fields:
            display_label = field.custom_label if field.custom_label else field.field_label
            
            field_dict = {
                'name': field.field_name,
                'label': display_label,
                'type': field.field_type,
                'required': field.is_required,
                'category': field.field_category,
                'has_dropdown': field.dropdown_enabled,
                'dropdown_category': field.dropdown_category
            }
            
            result.append(field_dict)
            
            # Print field info
            print(f"Field: {field.field_name}")
            print(f"  label: {display_label}")
            print(f"  has_dropdown: {field_dict['has_dropdown']} (type: {type(field_dict['has_dropdown']).__name__})")
            print(f"  dropdown_category: {field_dict['dropdown_category']} (type: {type(field_dict['dropdown_category']).__name__ if field_dict['dropdown_category'] else 'None'})")
            
            # Test the condition
            if field_dict['has_dropdown'] and field_dict['dropdown_category']:
                print(f"  ✅ WOULD SHOW DROPDOWN")
            else:
                print(f"  ❌ WOULD NOT SHOW (has_dropdown={field_dict['has_dropdown']}, category={field_dict['dropdown_category']})")
            print()
        
        print("="*80)
        print("🎯 SUMMARY")
        print("="*80 + "\n")
        
        dropdown_count = sum(1 for f in result if f['has_dropdown'] and f['dropdown_category'])
        print(f"Total enabled fields: {len(result)}")
        print(f"Fields that SHOULD show dropdown: {dropdown_count}")
        
        if dropdown_count == 0:
            print("\n⚠️  WARNING: No fields will show dropdowns!")
            print("   Check if dropdowns are properly configured in settings.")
        
        print()
        
    finally:
        db.close()

if __name__ == "__main__":
    test_field_config()
