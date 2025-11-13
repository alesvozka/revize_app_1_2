# 🐛 OPRAVA DROPDOWN PROBLÉMU

## Problém
Dropdowny se nezobrazují ve formulářích, i když jsou v nastavení "zapnuté".

## Příčina
V Revize App existují **DVA RŮZNÉ nastavení** pro každé pole:

1. **🔽 Dropdown konfigurace** (`dropdown_enabled`)
   - Zapíná/vypíná dropdown widget pro pole
   - Vyžaduje výběr kategorie (`dropdown_category`)

2. **👁️ Viditelnost pole** (`enabled`)
   - Určuje, jestli se pole VŮBEC zobrazí ve formuláři
   - Pokud je `enabled=False`, pole se nezobrazí (ani s dropdownem!)

### Co se stalo?
Když redesignoval Chat aplikaci, pravděpodobně:
- Zapnul jsi dropdowny (`dropdown_enabled=True`) ✅
- Ale pole zůstala SKRYTÁ (`enabled=False`) ❌

→ **Výsledek:** Widget se nezobrazí, protože celé pole je neviditelné!

## 🔧 Řešení

### Automatická oprava (DOPORUČENO)
Spusť fix script, který automaticky zapne viditelnost pro všechna pole s dropdownem:

```bash
python fix_dropdown_visibility.py
```

### Manuální oprava
1. Otevři aplikaci a jdi do `/settings`
2. Přepni na záložku **"👁️ Viditelnost polí"**
3. Pro každou entitu (Revize, Rozváděč, Přístroj, atd.):
   - Najdi pole, které má mít dropdown
   - Zapni toggle u těch polí (mělo by svítit zeleně)
4. Vrať se do záložky **"🔽 Dropdown konfigurace"**
5. Zkontroluj, že:
   - Checkbox "Enable dropdown" je zaškrtnutý ✅
   - Je vybrána kategorie ze selectu ✅
   - Kliknuté "💾 Uložit" ✅

### Diagnostika
Pokud si nejsi jistý, co je v databázi, spusť diagnostic script:

```bash
python check_dropdowns.py
```

Ten ti ukáže:
- Která pole jsou viditelná
- Která pole mají dropdown
- Kde jsou problémy (dropdown zapnutý, ale pole skryté)

## 📊 Co bylo opraveno v kódu

### 1. Bug v `form_field_dynamic.html`
- **Problém:** Chybějící `current_value` → pole prázdná
- **Oprava:** Přidána proměnná `current_value` před include widgetu

### 2. Bug v `settings_redesigned.html`
- **Problém:** Disabled select nepošle hodnotu → `dropdown_category=None`
- **Oprava:** JavaScript `toggleDropdownConfig` automaticky vybere první kategorii

### 3. Bug v `main.py` endpoint `/settings/dropdown-config/update`
- **Problém:** `dropdown_enabled=True` ale `dropdown_category=None`
- **Oprava:** Server validace - pokud chybí kategorie, dropdown se vypne

### 4. Debug výpisy v `get_entity_field_config`
- Přidány výpisy, které ukazují, kolik polí má dropdown
- Pomáhá diagnostikovat problémy

## 🎯 Kontrola, že to funguje

Po opravě:
1. Otevři formulář (např. vytvoř nový přístroj)
2. U polí s dropdownem by měla být:
   - Input pole (můžeš psát přímo)
   - Šipka vpravo (kliknutím otevřeš dropdown)
   - Dropdown menu s hodnotami z databáze
   - Možnost "Přidat novou hodnotu..."

Pokud to nevidíš, spusť `check_dropdowns.py` pro diagnostiku!

---

**Vytvořeno:** $(date +"%Y-%m-%d")
**Opravené verze:** form_field_dynamic.html, settings_redesigned.html, main.py
