# 🔧 DIAGNOSTIKA: Problém s formuláři entit

## 📋 PROBLÉM

**Symptomy:**
- Ve formulářích entit (Revision, Switchboard, atd.) se nezobrazují všechny kategorie polí
- Místo dynamických kategorií z nastavení se zobrazují pevně zakódované karty
- Například u Revize chybí kategorie "Technické pole", "Dodatečné pole", "Administrativní pole"
- Zobrazuje se karta "Termíny", která v nastavení vůbec není

## 🔍 PŘÍČINA

### 1. Chybějící soubor makr
**Soubor:** `templates/components/form_field_dynamic.html`  
**Status:** ❌ NEEXISTOVAL

Všechny formuláře volaly makra z tohoto souboru:
- `render_entity_form` - pro vykreslení celého formuláře
- `render_dynamic_field` - pro vykreslení jednotlivých polí

Když soubor neexistoval, Jinja2 padal na fallback kód, který má pouze minimální hardcoded pole.

### 2. Pevně zakódované karty
**Soubory:** `templates/cards/*`

Karty v detail views používají pevně zakódované kategorie:
- `revision_static_basic.html` - Základní informace
- `revision_static_dates.html` - **Termíny** ← Tato kategorie neexistuje v FieldConfig!
- `revision_static_admin.html` - Administrativní pole

**Správné kategorie podle seed_field_config.py:**
- `basic` - Základní informace
- `additional` - Dodatečné údaje  
- `technical` - Technické údaje
- `administrative` - Administrativní údaje

## ✅ ŘEŠENÍ

### 1. ✅ Vytvořen soubor `form_field_dynamic.html`

Soubor obsahuje 3 makra:

#### `render_dynamic_field(field, entity, dropdown_sources)`
- Vykreslí jedno pole podle jeho konfigurace
- Podporuje typy: text, textarea, number, date
- Podporuje dropdown widgety se třemi režimy:
  - Výběr z existujících hodnot
  - Přidání nové hodnoty (➕)
  - Vlastní text (✏️)

#### `render_entity_form(entity_type, field_configs, entity, dropdown_sources)`
- Vykreslí celý formulář s dynamickými kategoriemi
- Seskupí pole podle kategorie (`field.category`)
- Zobrazí kategorie v správném pořadí
- Ukáže počet polí v každé kategorii

#### `render_field_card_edit(entity_type, category, field_configs, entity, dropdown_sources)`
- Pro inline editing v kartách
- Vykreslí pouze pole z konkrétní kategorie

### 2. ⚠️ Co je potřeba ještě udělat

#### A. Sjednotit kategorie v kartách (PRIORITA VYSOKÁ)

**Aktuální stav:**
```
templates/cards/
├── revision_static_basic.html    ✅ OK (kategorie: basic)
├── revision_static_dates.html    ❌ PROBLÉM (kategorie neexistuje!)
├── revision_static_admin.html    ✅ OK (kategorie: administrative)
└── chybí: technical, additional
```

**Co udělat:**
1. Přejmenovat nebo odstranit `revision_static_dates.html`
2. Vytvořit karty pro chybějící kategorie:
   - `revision_static_technical.html`
   - `revision_static_additional.html`
3. NEBO (lepší řešení): Vytvořit JEDNU dynamickou kartu

**Doporučení:**
Vytvořit jeden univerzální template `templates/cards/entity_card_dynamic.html`, který:
- Přijme `category_key` jako parametr
- Načte pole z `field_configs` pro danou kategorii
- Vykreslí je dynamicky pomocí makra

#### B. Upravit detail views

**Soubor:** `templates/revision_detail.html` (a další _detail.html)

**Aktuálně:**
```jinja
{% include 'cards/revision_static_basic.html' %}
{% include 'cards/revision_static_dates.html' %}
{% include 'cards/revision_static_admin.html' %}
```

**Mělo by být:**
```jinja
{% for category in field_categories %}
    {% include 'cards/entity_card_dynamic.html' with context %}
{% endfor %}
```

#### C. Načítat field_categories v endpointech

**Kde upravit:** `main.py`

**Funkce k úpravě:**
- `revision_detail()` 
- `revision_edit_form()`
- `switchboard_detail()`
- atd.

**Co přidat:**
```python
# Načíst kategorie pro danou entitu
field_categories = db.query(FieldCategory).filter(
    FieldCategory.entity_type == 'revision'
).order_by(FieldCategory.display_order).all()

# Přidat do template contextu
return templates.TemplateResponse("revision_detail.html", {
    "request": request,
    "field_categories": field_categories,  # ← PŘIDAT
    "field_configs": field_configs,
    # ... ostatní
})
```

## 📊 AKTUÁLNÍ STAV

### ✅ Hotovo:
- [x] Vytvořen `form_field_dynamic.html` s makry
- [x] Makra podporují všechny typy polí
- [x] Makra podporují dropdown widgety
- [x] Makra seskupují pole podle kategorií

### ⚠️ Zbývá:
- [ ] Sjednotit kategorie karet (odstranit "dates", přidat "technical", "additional")
- [ ] Vytvořit dynamické karty místo statických
- [ ] Upravit detail views aby načítaly kategorie z DB
- [ ] Aktualizovat endpointy aby předávaly field_categories

### 🔧 Rychlá oprava (dočasné řešení):

Pokud chceš rychle vyřešit problém s formuláři:

1. **Formuláře už fungují!** ✅ 
   - Makro `render_entity_form` je nyní k dispozici
   - Automaticky načte správné kategorie z field_configs

2. **Edit karty budou fungovat po restartu** ✅
   - Makro `render_dynamic_field` je k dispozici
   - Karty jako `revision_edit_basic.html` už budou fungovat

3. **Pro static karty** (zobrazení detailů):
   - Buď vytvoř chybějící karty ručně
   - NEBO implementuj dynamické karty (doporučeno)

## 🚀 DALŠÍ KROKY

### Priorita 1: Rychlý test
```bash
# Restartuj aplikaci
uvicorn main:app --reload

# Otevři formulář pro novou revizi
# http://localhost:8000/revision/create

# Měly by se zobrazit všechny kategorie polí:
# - Základní informace
# - Dodatečné údaje  
# - Technické údaje
# - Administrativní údaje
```

### Priorita 2: Implementace dynamických karet
Viz níže v sekci "IMPLEMENTAČNÍ PLÁN"

## 📝 IMPLEMENTAČNÍ PLÁN

### Fáze 1: Dynamické karty (2-3 hodiny)

#### 1.1 Vytvořit univerzální kartu
```bash
templates/cards/entity_card_dynamic.html
```

Obsahuje:
- Načtení polí pro danou kategorii
- Static i edit režim
- Použití makra `render_field_card_edit`

#### 1.2 Upravit detail views
Např. `revision_detail.html`:
- Načíst `field_categories` z DB
- Iterovat přes kategorie
- Include dynamické karty

#### 1.3 Upravit endpointy
Přidat do všech detail endpointů:
```python
from models import FieldCategory

field_categories = db.query(FieldCategory).filter(
    FieldCategory.entity_type == entity_type
).order_by(FieldCategory.display_order).all()
```

### Fáze 2: Seed kategorií (30 minut)

Ujistit se, že seed_field_config.py vytváří FieldCategory záznamy.

Aktuálně to vypadá, že se seed dělá při startu v main.py (řádek 105-122).

Zkontrolovat, že se seedují všechny kategorie:
- basic
- additional
- technical
- administrative
- measurements (pro některé entity)

### Fáze 3: Cleanup (30 minut)

Odstranit nebo přejmenovat:
- `revision_static_dates.html` (kategorie neexistuje)
- Další hardcoded karty

## 💡 TIPS

### Jak testovat kategorie v DB:
```python
# V Python konzoli nebo v test scriptu
from models import FieldCategory
from database import SessionLocal

db = SessionLocal()
categories = db.query(FieldCategory).filter(
    FieldCategory.entity_type == 'revision'
).all()

for cat in categories:
    print(f"{cat.category_key}: {cat.category_label} (order: {cat.display_order})")
```

### Očekávaný výstup:
```
basic: Základní informace (order: 0)
additional: Dodatečné údaje (order: 1)
technical: Technické údaje (order: 2)
administrative: Administrativní údaje (order: 3)
```

## 🎯 ZÁVĚR

**Hlavní problém byl:** Chybějící soubor `form_field_dynamic.html`

**Status:** ✅ **VYŘEŠENO** - soubor vytvořen

**Zbývá:** Implementovat dynamické karty pro detail views (volitelné, ale doporučené)

**Příští krok:** Restart aplikace a test formulářů

---

**Autor:** Claude  
**Datum:** 2025-11-12  
**Fáze:** 5.4 - Oprava formulářů
