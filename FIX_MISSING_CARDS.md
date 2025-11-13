# 🔧 OPRAVA FORMULÁŘŮ - CHYBĚJÍCÍ KARTY KATEGORIÍ

## 🔍 Problém

**Symptomy:**
- Ve formuláři pro vytvoření/editaci Revize **chybí karty** pro kategorie:
  - ❌ Technické údaje
  - ❌ Dodatečné údaje (jen některá pole)
  - ❌ Administrativní údaje (jen některá pole)
- V detailu revize se zobrazuje hardcoded karta **"Termíny"**, která není v Nastavení

**Proč se to děje:**

1. **Formuláře jsou dynamické** - generují se podle konfigurace v tabulce `dropdown_config`
2. **Funkce `get_entity_field_config()` filtruje jen `enabled=True` pole**
3. **Mnohá pole jsou v seed datech nastavena jako `enabled=False`:**

```python
# V seed_field_config.py:

# Administrativa - většina DISABLED
('revision_number_of_copies_technician', ..., False, ...)  # ❌ DISABLED
('revision_number_of_copies_owner', ..., False, ...)       # ❌ DISABLED
('revision_technician', ..., True, ...)                     # ✅ ENABLED

# Technické - všechna DISABLED
('revision_measuring_instrument_manufacturer_type', ..., False, ...)  # ❌ DISABLED
('revision_measuring_instrument_serial_number', ..., False, ...)      # ❌ DISABLED
('revision_overall_assessment', ..., False, ...)                      # ❌ DISABLED
```

**Výsledek:**
- Pokud kategorie nemá žádné enabled pole → **karta se NEzobrazí**
- Funkce `render_entity_form` generuje karty jen pro kategorie s enabled poli

---

## ✅ Řešení

### Metoda 1: Rychlé řešení - Enable všech polí scriptem

```bash
# 1. Zkontroluj aktuální stav
python check_field_visibility.py

# 2. Enable všechna pole
python enable_all_fields.py

# 3. Restartuj aplikaci
uvicorn main:app --reload

# 4. Zkontroluj formulář - měly by se zobrazit všechny karty!
```

### Metoda 2: Manuální enable v Nastavení

1. Otevři **Nastavení → Viditelnost polí → Revize**
2. Pro každé disabled pole (šedé) klikni na **checkbox** pro enable
3. Pole se automaticky zobrazí ve formuláři

### Metoda 3: Změna seed dat (trvalé řešení)

Uprav `seed_field_config.py` a změň `False` na `True` u polí, která chceš zobrazit:

```python
# PŘED:
('revision_measuring_instrument_manufacturer_type', 'Výrobce/typ měřicího přístroje', 'technical', 'text', False, False, 400),

# PO:
('revision_measuring_instrument_manufacturer_type', 'Výrobce/typ měřicího přístroje', 'technical', 'text', True, False, 400),
#                                                                                                            ^^^^
#                                                                                                           enabled
```

Pak znovu spusť seed:
```bash
python seed_field_config.py
```

---

## 📊 Co skripty dělají

### `check_field_visibility.py`
```bash
python check_field_visibility.py
```

**Výstup:**
```
🔍 KONTROLA VIDITELNOSTI POLÍ
=======================================

📋 Základní informace
  Status: ✅ ZOBRAZÍ SE
  Enabled polí: 5/5
  Disabled polí: 0/5

📝 Dodatečné údaje
  Status: ✅ ZOBRAZÍ SE
  Enabled polí: 6/7
  Disabled polí: 1/7
  
  Disabled pole:
    - revision_date_of_previous_revision (Datum předchozí revize)

🔧 Technické údaje
  Status: ❌ NEZOBRAZÍ SE
  Enabled polí: 0/5
  Disabled polí: 5/5
  
  Disabled pole:
    - revision_measuring_instrument_manufacturer_type (Výrobce/typ měřicího přístroje)
    - revision_measuring_instrument_serial_number (Výrobní číslo měřicího přístroje)
    - revision_measuring_instrument_calibration (Kalibrace přístroje)
    - revision_measuring_instrument_calibration_validity (Platnost kalibrace)
    - revision_overall_assessment (Celkové hodnocení)
```

### `enable_all_fields.py`
```bash
# Enable všechna pole
python enable_all_fields.py --all

# Enable jen důležité kategorie (basic, additional, technical, administrative)
python enable_all_fields.py --important-only

# Enable pro jinou entitu
python enable_all_fields.py --entity switchboard --all
```

---

## 🎯 Jak funguje generování formulářů

### 1. Načtení konfigurace
```python
# main.py: revision_create_form()
field_configs = get_entity_field_config('revision', db)
```

### 2. Filtrování enabled polí
```python
# main.py: get_entity_field_config()
fields = db.query(DropdownConfig).filter(
    DropdownConfig.entity_type == entity_type,
    DropdownConfig.enabled == True  # ← KLÍČOVÝ FILTR!
).order_by(DropdownConfig.display_order).all()
```

### 3. Generování karet podle kategorií
```python
# components/form_field_dynamic.html: render_entity_form()
# Seskupí pole podle field_category
# Pro každou kategorii s poli vytvoří kartu:
#   - basic → 📋 Základní informace
#   - additional → 📝 Dodatečné údaje
#   - technical → 🔧 Technické údaje
#   - administrative → 📄 Administrativní údaje
```

**Pokud kategorie nemá žádné enabled pole → karta se NEgeneruje!**

---

## 🆚 Rozdíl: Formulář vs. Detail view

### Formulář (`revision_form.html`)
- ✅ **Dynamické karty** podle field_config
- ✅ Respektuje enabled/disabled v nastavení
- ✅ Lze ovládat v Nastavení → Viditelnost polí

### Detail view (`revision_detail_redesigned.html`)
- ⚠️ **Hardcoded karty** (Základní, Termíny, Administrativní)
- ⚠️ NErespektuje field_config
- ⚠️ Karta "Termíny" NENÍ v nastavení

**Poznámka:** Detail view používá statické templaty z `cards/`:
- `cards/revision_static_basic.html`
- `cards/revision_static_dates.html` ← Termíny
- `cards/revision_static_admin.html`

---

## 🔮 Budoucí vylepšení

### Priorita 1: Dynamic static cards
Upravit detail view, aby respektoval enabled/disabled z nastavení:

```python
# Místo hardcoded templateů
template_name = f"cards/revision_static_{card_type}.html"

# Generovat karty dynamicky podle field_config
if category has enabled fields:
    show card
else:
    hide card
```

### Priorita 2: Unifikace kategorií
Sjednotit kategorie mezi:
- Formulářem (basic, additional, technical, administrative)
- Detail view (basic, dates, admin)

Navržená struktura:
- basic → Základní informace
- additional → Dodatečné údaje
- dates → Termíny (nová kategorie!)
- technical → Technické údaje
- administrative → Administrativní údaje

---

## 📝 Checklist opravy

- [ ] Spustit `python check_field_visibility.py` - diagnostika
- [ ] Spustit `python enable_all_fields.py` - oprava
- [ ] Restartovat aplikaci
- [ ] Otevřít formulář Nová revize
- [ ] Zkontrolovat, že se zobrazují všechny karty:
  - [ ] 📋 Základní informace
  - [ ] 📝 Dodatečné údaje
  - [ ] 🔧 Technické údaje
  - [ ] 📄 Administrativní údaje

---

## 🆘 Pokud to nefunguje

1. Zkontroluj databázi:
```bash
python check_database.py
```

2. Zkontroluj field_config:
```bash
python check_dropdown_sources.py
```

3. Zkontroluj výstup v konzoli při spuštění:
```bash
uvicorn main:app --reload
```

Hledej řádky:
```
🔍 DEBUG get_entity_field_config(revision): X viditelných polí
```

---

**✨ Po opravě by se měly všechny karty zobrazit ve formuláři!**
