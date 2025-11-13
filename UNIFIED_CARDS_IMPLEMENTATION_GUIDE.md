# 🎯 UNIFIED CARDS SYSTEM - IMPLEMENTAČNÍ PRŮVODCE

## 📋 Přehled

Tento průvodce tě provede kompletní unifikací systému karet v Revize App.

**Před unifikací:**
- ❌ Dva různé systémy (hardcoded karty vs. dynamické)
- ❌ Nekonzistentní kategorie
- ❌ Bugy v templates (neexistující pole)
- ❌ Detail view ignoruje field_config

**Po unifikaci:**
- ✅ Jeden unified systém
- ✅ Stejné kategorie všude
- ✅ Dynamické generování podle field_config
- ✅ Respektování enabled/disabled
- ✅ Žádné duplicity kódu

---

## 🚀 Implementace (5 kroků)

### Krok 1: Migrace kategorií polí

Spusť migration script, který přesune pole do nových unified kategorií:

```bash
# Dry run - kontrola změn bez uložení
python migrate_field_categories.py --dry-run

# Reálná migrace
python migrate_field_categories.py
```

**Co to dělá:**
- Přidá kategorii "dates" (Termíny)
- Přesune pole do správných kategorií:
  - basic → revision_code, revision_name, revision_owner, revision_client, revision_address, revision_type, revision_description, revision_short_description
  - dates → všechna datum pole
  - technical → measuring instrument pole + overall_assessment
  - administrative → technician, certificates, attachments, copies
- Zruší kategorii "additional" (pole přesunuta do basic a dates)
- Enable všechna pole

**Výstup:**
```
🔄 MIGRACE FIELD CATEGORIES
=======================================

📋 Základní informace (basic)
  revision_code: administrative → basic
  revision_type: additional → basic
  revision_description: additional → basic
  revision_short_description: administrative → basic

📅 Termíny (dates)
  revision_date_of_creation: additional → dates
  revision_start_date: additional → dates
  ...

✅ MIGRACE DOKONČENA
Pole přesunuta: 15
Pole enabled: 32
```

---

### Krok 2: Aktualizace templates

#### A) Nové komponenty (už vytvořené)
- ✅ `templates/components/dynamic_cards.html` - makra pro dynamické karty
- ✅ `templates/revision_detail_unified.html` - nový unified detail view

#### B) Oprava static card templates

**Soubor:** `templates/cards/revision_static_admin.html`

**PŘED (buggy - odkazuje na neexistující pole):**
```html
{% if revision.ico %}
<div>
    <dt>IČO</dt>
    <dd>{{ revision.ico }}</dd>
</div>
{% endif %}
```

**PO (opraveno - jen existující pole):**
```html
{% if revision.revision_code %}
<div>
    <dt>Kód revize</dt>
    <dd>{{ revision.revision_code }}</dd>
</div>
{% endif %}

{% if revision.revision_technician %}
<div>
    <dt>Technik</dt>
    <dd>{{ revision.revision_technician }}</dd>
</div>
{% endif %}

{% if revision.revision_project_documentation %}
<div>
    <dt>Projektová dokumentace</dt>
    <dd>{{ revision.revision_project_documentation }}</dd>
</div>
{% endif %}
```

**NEBO** (ještě lepší - použít dynamické makro):**
```html
{% from 'components/dynamic_cards.html' import render_static_card %}
{{ render_static_card('administrative', field_configs, revision, 'card-admin') }}
```

#### C) Vytvoření technical karty

**Nový soubor:** `templates/cards/revision_static_technical.html`

```html
{% from 'components/dynamic_cards.html' import render_static_card %}
{{ render_static_card('technical', field_configs, revision, 'card-technical') }}
```

**Nový soubor:** `templates/cards/revision_edit_technical.html`

```html
{% from 'components/form_field_dynamic.html' import render_field_card_edit %}

<form 
    hx-post="/revision/{{ revision.revision_id }}/update-card/technical"
    hx-target="#card-technical"
    hx-swap="outerHTML"
    class="p-4">
    
    {{ render_field_card_edit('revision', 'technical', field_configs, revision, dropdown_sources) }}
    
    <div class="flex gap-2 mt-4 pt-4 border-t">
        <button type="submit" class="px-4 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark">
            💾 Uložit
        </button>
        <button 
            type="button"
            hx-get="/revision/{{ revision.revision_id }}/card/technical"
            hx-target="#card-technical"
            hx-swap="outerHTML"
            class="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50">
            Zrušit
        </button>
    </div>
</form>
```

---

### Krok 3: Update main.py

Aplikuj změny z `PATCH_MAIN_UNIFIED_CARDS.py`:

#### A) Revision detail endpoint

**Najdi řádek ~635:**
```python
@app.get("/revision/{revision_id}", response_class=HTMLResponse)
async def revision_detail(revision_id: int, request: Request, db: Session = Depends(get_db)):
```

**Přidej načtení field_configs:**
```python
# PHASE 6: Load field configs pro dynamické karty
field_configs = get_entity_field_config('revision', db)

# Load dropdown sources
categories = db.query(DropdownSource.category).distinct().all()
dropdown_sources = {}
for cat in categories:
    category = cat[0]
    sources = db.query(DropdownSource).filter(
        DropdownSource.category == category
    ).order_by(DropdownSource.display_order, DropdownSource.value).all()
    dropdown_sources[category] = sources
```

**Změň template:**
```python
return templates.TemplateResponse("revision_detail_unified.html", {  # ← změna
    "request": request,
    "user_id": user_id,
    "revision": revision,
    "field_configs": field_configs,           # ← nové
    "dropdown_sources": dropdown_sources,     # ← nové
    "sidebar_revisions": get_sidebar_revisions(db, user_id),
    "current_revision_for_sidebar": revision
})
```

#### B) Get revision card endpoint

**Najdi řádek ~656:**
```python
@app.get("/revision/{revision_id}/card/{card_type}", response_class=HTMLResponse)
async def get_revision_card(revision_id: int, card_type: str, ...
```

**Přidej field_configs:**
```python
# PHASE 6: Load field configs pro dynamické static karty
field_configs = get_entity_field_config('revision', db)

template_name = f"cards/revision_static_{card_type}.html"
return templates.TemplateResponse(template_name, {
    "request": request,
    "revision": revision,
    "field_configs": field_configs  # ← nové
})
```

#### C) Update card endpoint

**Najdi řádek ~711 s update_revision_card:**

**Přidej podporu pro technical kategorii:**
```python
elif card_type == 'technical':
    revision.revision_measuring_instrument_manufacturer_type = get_value("revision_measuring_instrument_manufacturer_type")
    revision.revision_measuring_instrument_serial_number = get_value("revision_measuring_instrument_serial_number")
    revision.revision_measuring_instrument_calibration = get_value("revision_measuring_instrument_calibration")
    revision.revision_measuring_instrument_calibration_validity = get_value("revision_measuring_instrument_calibration_validity")
    revision.revision_overall_assessment = get_value("revision_overall_assessment")
```

---

### Krok 4: Testování

```bash
# 1. Zkontroluj field_config
python check_field_visibility.py

# Očekávaný výstup:
# 📋 Základní informace: ✅ ZOBRAZÍ SE (8 polí)
# 📅 Termíny: ✅ ZOBRAZÍ SE (5 polí)
# 🔧 Technické údaje: ✅ ZOBRAZÍ SE (5 polí)
# 📄 Administrativní údaje: ✅ ZOBRAZÍ SE (14 polí)

# 2. Restartuj aplikaci
uvicorn main:app --reload

# 3. Otevři revision detail
# http://localhost:8000/revision/1

# 4. Zkontroluj, že se zobrazují všechny karty:
#    - 📋 Základní informace
#    - 📅 Termíny
#    - 🔧 Technické údaje (collapsible)
#    - 📄 Administrativní údaje (collapsible)
#    - 📦 Rozváděče

# 5. Zkontroluj formulář
# http://localhost:8000/revision/new

# 6. Měl by zobrazovat stejné karty jako detail view!
```

---

### Krok 5: Rozšíření na další entity

Po úspěšné unifikaci revize, aplikuj stejný systém na:

1. **Switchboard**
   - Vytvoř `switchboard_detail_unified.html`
   - Uprav switchboard endpointy v main.py
   - Migruj switchboard field categories

2. **Device, Circuit, Terminal Device**
   - Stejný postup
   - Unified struktura pro všechny entity

---

## ✅ Checklist implementace

- [ ] Spustit `migrate_field_categories.py`
- [ ] Zkontrolovat výstup - všechna pole přesunuta
- [ ] Opravit `revision_static_admin.html` (odstranit neexistující pole)
- [ ] Vytvořit `revision_static_technical.html`
- [ ] Vytvořit `revision_edit_technical.html`
- [ ] Upravit `revision_detail` endpoint v main.py
- [ ] Upravit `get_revision_card` endpoint v main.py
- [ ] Upravit `update_revision_card` endpoint v main.py
- [ ] Restartovat aplikaci
- [ ] Otevřít revision detail - zkontrolovat 4 karty
- [ ] Otevřít revision form - zkontrolovat 4 karty
- [ ] Test edit v kartách - zkontrolovat, že funguje
- [ ] Test collapse technické/administrativní karty
- [ ] Zkontrolovat, že disabled pole se nezobrazují

---

## 🎯 Výsledek

Po dokončení implementace:

✅ **Unified systém**
- Jedna konfigurace (field_config) pro všechno
- Stejné kategorie v detailu i formuláři
- Dynamické generování karet

✅ **Čisté templates**
- Žádné hardcoded karty
- Žádné duplicity
- Žádná neexistující pole

✅ **Flexibilita**
- Vše lze měnit v Nastavení
- Enable/disable polí
- Přejmenování polí
- Změna pořadí

✅ **Konzistence**
- Formuláře = Detail view
- Revision = Switchboard = Device = ...

---

## 📚 Reference

- `ANALYSIS_CARD_STRUCTURE.md` - Detailní analýza současného stavu
- `migrate_field_categories.py` - Migration script
- `templates/components/dynamic_cards.html` - Makra pro karty
- `templates/revision_detail_unified.html` - Nový unified template
- `PATCH_MAIN_UNIFIED_CARDS.py` - Změny pro main.py

---

**✨ Po unifikaci budeš mít čistý, konzistentní systém bez duplicit a bugů!**
