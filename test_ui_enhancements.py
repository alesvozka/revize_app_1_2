#!/usr/bin/env python3
"""
Test script pro kontrolu UI vylepšení v settings_redesigned.html
"""

def check_settings_template():
    """Kontrola, že settings template má všechny potřebné části"""
    
    with open('templates/settings_redesigned.html', 'r', encoding='utf-8') as f:
        content = f.read()
    
    checks = {
        "Edit button pro dropdown hodnoty": "openEditValueModal",
        "Move up button pro pole": "moveFieldUp",
        "Move down button pro pole": "moveFieldDown",
        "Rename button pro pole": "openRenameFieldModal",
        "Rename field modal": 'id="rename-field-modal"',
        "Edit value modal": 'id="edit-value-modal"',
        "submitRenameField funkce": "async function submitRenameField",
        "submitEditValue funkce": "async function submitEditValue",
        "closeRenameFieldModal funkce": "function closeRenameFieldModal",
        "closeEditValueModal funkce": "function closeEditValueModal",
    }
    
    print("🔍 KONTROLA SETTINGS TEMPLATE")
    print("=" * 60)
    
    all_ok = True
    for name, pattern in checks.items():
        found = pattern in content
        status = "✅" if found else "❌"
        print(f"{status} {name}")
        if not found:
            all_ok = False
    
    print("=" * 60)
    if all_ok:
        print("🎉 Všechny komponenty jsou přítomné!")
    else:
        print("⚠️  Některé komponenty chybí!")
    
    return all_ok


def check_backend_endpoints():
    """Kontrola, že backend má všechny potřebné endpointy"""
    
    with open('main.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    endpoints = {
        "Move field up": '@app.post("/settings/field-config/{field_id}/move-up")',
        "Move field down": '@app.post("/settings/field-config/{field_id}/move-down")',
        "Rename field": '@app.post("/settings/field-config/{field_id}/rename")',
        "Edit dropdown value": '@app.post("/settings/dropdown/value/{value_id}/edit")',
    }
    
    print("\n🔍 KONTROLA BACKEND ENDPOINTŮ")
    print("=" * 60)
    
    all_ok = True
    for name, pattern in endpoints.items():
        found = pattern in content
        status = "✅" if found else "❌"
        print(f"{status} {name}")
        if not found:
            all_ok = False
    
    print("=" * 60)
    if all_ok:
        print("🎉 Všechny endpointy jsou přítomné!")
    else:
        print("⚠️  Některé endpointy chybí!")
    
    return all_ok


def main():
    print("🚀 TEST UI VYLEPŠENÍ - FÁZE 5.3")
    print("\n")
    
    template_ok = check_settings_template()
    backend_ok = check_backend_endpoints()
    
    print("\n" + "=" * 60)
    if template_ok and backend_ok:
        print("✅ VŠECHNY TESTY PROŠLY!")
        print("\n📋 DALŠÍ KROKY:")
        print("1. Spusť aplikaci: uvicorn main:app --reload")
        print("2. Otevři nastavení: http://localhost:8000/settings")
        print("3. Vyzkoušej:")
        print("   - ✏️ Editace dropdown hodnoty")
        print("   - ↑/↓ Změna pořadí polí")
        print("   - ✏️ Přejmenování pole")
    else:
        print("❌ NĚKTERÉ TESTY SELHALY!")
        print("Zkontroluj výše uvedené chybějící komponenty.")
    print("=" * 60)


if __name__ == "__main__":
    main()
