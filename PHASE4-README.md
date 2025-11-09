# 🎯 PHASE 4: CONFIGURABLE FIELDS SYSTEM

## 📋 PŘEHLED

Phase 4 přidává systém konfigurovatelných polí, který umožňuje uživatelům zapnout/vypnout pole ve formulářích podle jejich workflow. Tím se redukuje počet zobrazených polí a zrychluje vyplňování formulářů.

### Před Phase 4:
- ❌ Formulář Revize: **29 polí** (všechna povinně zobrazená)
- ❌ Čas vyplnění: ~5 minut
- ❌ Vyplněno: ~10 polí (65% prázdných)

### Po Phase 4:
- ✅ Formulář Revize: **8-12 polí** (jen zapnutá podle workflow)
- ✅ Čas vyplnění: ~2 minuty  
- ✅ Vyplněno: ~8-12 polí (0% prázdných)

---

## 🚀 NOVÉ FUNKCE

### 1. Field Visibility Configuration

Nová sekce v Settings umožňuje:
- ✅ **Zapnout/vypnout pole** pro každou entitu (Revize, Rozváděč, Přístroj, Obvod, Terminál)
- ✅ **Změnit pořadí** zobrazení polí (display_order)
- ✅ **Ochrana povinných polí** - základní pole nelze vypnout
- ✅ **Hromadné akce** - zapnout/vypnout všechna dodatečná pole najednou

### 2. Dynamický Rendering Formulářů

- ✅ Formuláře se automaticky renderují podle konfigurace
- ✅ Zobrazují se pouze zapnutá pole
- ✅ Respektuje pořadí nastavené uživatelem
- ✅ Zachovává dropdown konfiguraci z Phase 2-3

### 3. Per-User Configuration (připraveno)

Model je připraven pro per-user konfiguraci - každý uživatel bude moci mít vlastní nastavení polí.

---

## 📁 STRUKTURA SOUBORŮ

### Nové soubory:
```
/migrate_phase4.py                           # Migrační skript pro DB
/seed_field_config.py                        # Seed data pro field config
/templates/components/form_field_dynamic.html  # Dynamické renderování
```

### Upravené soubory:
```
/models.py                   # Rozšířený DropdownConfig model
/main.py                     # Nové API endpointy + helper funkce
/templates/settings.html     # Nová sekce pro field configuration
```

---

## 🗄️ DATABÁZOVÉ ZMĚNY

### Rozšíření `dropdown_config` tabulky:

```sql
ALTER TABLE dropdown_config ADD COLUMN field_label VARCHAR(255);
ALTER TABLE dropdown_config ADD COLUMN field_category VARCHAR(100);  -- 'basic', 'additional', 'measurements'
ALTER TABLE dropdown_config ADD COLUMN display_order INTEGER DEFAULT 0;
ALTER TABLE dropdown_config ADD COLUMN enabled BOOLEAN DEFAULT TRUE;
ALTER TABLE dropdown_config ADD COLUMN is_required BOOLEAN DEFAULT FALSE;
ALTER TABLE dropdown_config ADD COLUMN field_type VARCHAR(50) DEFAULT 'text';
```

---

## ⚙️ INSTALACE A MIGRACE

### Krok 1: Spuštění migrace
```bash
python migrate_phase4.py
```

### Krok 2: Naplnění seed dat
```bash
python seed_field_config.py
```

### Krok 3: Restart aplikace
```bash
# Railway / production
railway up

# Lokálně
uvicorn main:app --reload
```

---

## 📚 POUŽITÍ

### Pro uživatele:

1. **Otevřete Settings** (`/settings`)
2. **Přejděte na sekci** "Konfigurace viditelnosti polí"
3. **Vyberte entitu** (Revize, Rozváděč, ...)
4. **Zapněte/vypněte pole** podle vašeho workflow
5. **Změňte pořadí** pokud je to potřeba
6. **Uložte změny**

### Pro vývojáře:

#### Použití v API endpointech:

```python
from main import get_entity_field_config

@app.get("/revision/create")
async def revision_create_form(request: Request, db: Session = Depends(get_db)):
    # Get field configuration
    field_configs = get_entity_field_config('revision', db)
    
    return templates.TemplateResponse("revision_form.html", {
        "request": request,
        "field_configs": field_configs,
        "revision": None
    })
```

#### Použití v templates:

```html
{% from 'components/form_field_dynamic.html' import render_entity_form %}

<form method="POST">
  {{ render_entity_form('revision', field_configs, revision, dropdown_sources) }}
  
  <button type="submit">Uložit</button>
</form>
```

---

## 🔧 API ENDPOINTY

### GET `/api/form-config/{entity_type}`
Vrátí konfiguraci polí pro danou entitu (pouze enabled pole).

**Response:**
```json
{
  "entity_type": "revision",
  "fields": [
    {
      "name": "revision_name",
      "label": "Název revize",
      "type": "text",
      "required": true,
      "category": "basic",
      "has_dropdown": false,
      "dropdown_category": null
    },
    ...
  ]
}
```

### GET `/api/field-config/{entity_type}/all`
Vrátí VŠECHNA pole včetně vypnutých (pro settings page).

### POST `/settings/field-config/update`
Uloží změny v konfiguraci polí.

**Form data:**
```
field_enabled_{id}: on/off
field_order_{id}: number
```

### POST `/settings/field-config/{entity_type}/bulk-update`
Hromadné akce.

**Form data:**
```
action: enable_all | disable_all | reset_defaults
```

---

## 🎨 UI KOMPONENTY

### Field Configuration Manager

Nová sekce v Settings:
- 📋 Entity selector (Revize, Rozváděč, ...)
- ✅ Checkboxy pro zapnutí/vypnutí polí
- 🔢 Number inputy pro změnu pořadí
- 🚀 Hromadné akce (Zapnout vše / Vypnout vše)

### Dynamic Form Renderer

Nový template macro:
- `render_dynamic_field()` - vykreslí jedno pole
- `render_entity_form()` - vykreslí celý formulář entity

---

## 📊 FIELD CATEGORIES

### basic
Základní pole - většinou povinná, nelze vypnout
- Revize: `revision_name`, `revision_client`
- Rozváděč: `switchboard_name`, `switchboard_location`
- Přístroj: `switchboard_device_position`, `switchboard_device_type`

### additional
Dodatečná pole - volitelná, lze vypnout
- Většina ostatních polí

### measurements (budoucí)
Měřící pole - budou mít vlastní sekci

---

## ✅ TESTOVÁNÍ

### Test 1: Migrace a seed data
```bash
python migrate_phase4.py
python seed_field_config.py
```

**Očekávaný výsledek:**
- ✅ Tabulka `dropdown_config` má nové sloupce
- ✅ Všechny entity mají field configuration

### Test 2: Settings UI
1. Otevřete `/settings`
2. Rozbalte "Konfigurace viditelnosti polí"
3. Vyberte "Revize"

**Očekávaný výsledek:**
- ✅ Zobrazí se základní pole (disabled checkbox)
- ✅ Zobrazí se dodatečná pole (enabled checkbox)
- ✅ Lze změnit pořadí

### Test 3: Formulář
1. Vypněte nějaké pole v Settings
2. Otevřete `/revision/create`

**Očekávaný výsledek:**
- ✅ Vypnuté pole se nezobrazí
- ✅ Zapnutá pole jsou v nastaveném pořadí

### Test 4: Hromadné akce
1. Klikněte "Vypnout všechna dodatečná pole"
2. Uložte
3. Otevřete formulář

**Očekávaný výsledek:**
- ✅ Zobrazí se pouze základní povinná pole

---

## 🐛 TROUBLESHOOTING

### Problém: Migrace selhala
**Řešení:**
```bash
# Zkontrolujte zda existuje tabulka dropdown_config
# Zkontrolujte DB connection string v database.py
```

### Problém: Field config se nenačítá
**Řešení:**
```bash
# Zkontrolujte že seed_field_config.py byl spuštěn
# Zkontrolujte v DB zda existují záznamy v dropdown_config
```

### Problém: Formulář zobrazuje všechna pole
**Řešení:**
1. Zkontrolujte že endpoint používá `get_entity_field_config()`
2. Zkontrolujte že template používá `render_entity_form()`
3. Zkontrolujte v Settings že pole jsou správně nakonfigurována

---

## 🔮 BUDOUCÍ VYLEPŠENÍ

- [ ] **Per-user configuration** - každý uživatel vlastní nastavení
- [ ] **Field templates** - přednastavené profily (Bytové domy, Komerční, ...)
- [ ] **Import/Export konfigurace** - sdílení nastavení mezi uživateli
- [ ] **Conditional fields** - zobrazit pole pouze pokud jiné pole má určitou hodnotu
- [ ] **Field validation rules** - vlastní validace pro pole

---

## 📝 POZNÁMKY

- Základní povinná pole NELZE vypnout
- Změny se projeví okamžitě ve všech formulářích
- Dropdown konfigurace z Phase 2-3 zůstává zachována
- Field configuration je připravena pro multi-user support

---

## 👨‍💻 AUTOR

Phase 4 implementace: 2024-11
