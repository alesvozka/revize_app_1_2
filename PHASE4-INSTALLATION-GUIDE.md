# 🚀 PHASE 4 - INSTALLATION GUIDE

## ⚡ RYCHLÁ INSTALACE (5 minut)

### Krok 1: Backup databáze ⚠️
```bash
# DŮLEŽITÉ! Vždy zálohuj před migrací

# Lokální SQLite
cp revize.db revize.db.backup_phase4

# Railway PostgreSQL
railway pg:dump > backup_phase4_$(date +%Y%m%d).sql
```

---

### Krok 2: Spuštění migrace
```bash
python migrate_phase4.py
```

**Očekávaný output:**
```
Executing: ALTER TABLE dropdown_config ADD COLUMN IF NOT EXISTS field_label VARCHAR(255)
✓ Success
Executing: ALTER TABLE dropdown_config ADD COLUMN IF NOT EXISTS field_category VARCHAR(100)
✓ Success
Executing: ALTER TABLE dropdown_config ADD COLUMN IF NOT EXISTS display_order INTEGER DEFAULT 0
✓ Success
Executing: ALTER TABLE dropdown_config ADD COLUMN IF NOT EXISTS enabled BOOLEAN DEFAULT TRUE
✓ Success
Executing: ALTER TABLE dropdown_config ADD COLUMN IF NOT EXISTS is_required BOOLEAN DEFAULT FALSE
✓ Success
Executing: ALTER TABLE dropdown_config ADD COLUMN IF NOT EXISTS field_type VARCHAR(50) DEFAULT 'text'
✓ Success

✓ Phase 4 migration completed!
```

---

### Krok 3: Naplnění seed dat
```bash
python seed_field_config.py
```

**Očekávaný output:**
```
📋 Processing entity: revision
   ✓ Added: revision_name
   ✓ Added: revision_client
   ✓ Added: revision_code
   ... (celkem 29 polí)

📋 Processing entity: switchboard
   ✓ Added: switchboard_name
   ✓ Added: switchboard_location
   ... (celkem 26 polí)

📋 Processing entity: device
   ✓ Added: switchboard_device_position
   ... (celkem 7 polí)

📋 Processing entity: circuit
   ✓ Added: circuit_number
   ... (celkem 6 polí)

📋 Processing entity: terminal_device
   ✓ Added: terminal_device_type
   ... (celkem 8 polí)

✓ Field configurations seeded!
  Added: 76
  Updated: 0
```

---

### Krok 4: Restart aplikace
```bash
# Lokální development
uvicorn main:app --reload

# Railway / production
git add .
git commit -m "Phase 4: Configurable Fields System"
git push origin main
railway up
```

---

### Krok 5: Ověření instalace
```bash
# 1. Otevři aplikaci
http://localhost:8000  # nebo tvoje Railway URL

# 2. Jdi na Settings
http://localhost:8000/settings

# 3. Rozbal "Konfigurace viditelnosti polí"
# 4. Vyber "Revize"
# 5. Měl bys vidět seznam polí s checkboxy
```

**Očekávaný pohled:**
```
┌──────────────────────────────────────────┐
│ Konfigurace viditelnosti polí            │
│                                           │
│ [📋 Revize] [📦 Rozváděč] [🔌 Přístroj] │
│                                           │
│ ✓ Základní pole (povinná)                │
│   ☑ Název revize (POVINNÉ)               │
│   ☑ Klient (POVINNÉ)                     │
│                                           │
│ ✓ Dodatečná pole (volitelná)             │
│   ☑ Kód revize                           │
│   ☑ Vlastník                             │
│   ☐ Datum předchozí revize               │
│   ...                                     │
└──────────────────────────────────────────┘
```

---

## 🔧 TROUBLESHOOTING

### Problém: Migrace selhala s "column already exists"

**Řešení:**
```bash
# Zkontroluj zda migrace již nebyla provedena
python -c "
from database import SessionLocal
db = SessionLocal()
from models import DropdownConfig
import inspect
print([col.name for col in DropdownConfig.__table__.columns])
"

# Pokud sloupce již existují, přeskoč migraci
# Pokud ne, zkus migrace znovu
```

---

### Problém: Seed data selhala

**Řešení:**
```bash
# Zkontroluj connection string
cat database.py | grep SQLALCHEMY_DATABASE_URL

# Zkus seed znovu s debug outputem
python seed_field_config.py
```

---

### Problém: Field config se nezobrazuje v Settings

**Řešení:**
```bash
# 1. Check že seed proběhl
python -c "
from database import SessionLocal
from models import DropdownConfig
db = SessionLocal()
count = db.query(DropdownConfig).filter(
    DropdownConfig.field_label != None
).count()
print(f'Field configs: {count}')
"

# Očekávané: Field configs: 76

# 2. Check browser console
# F12 → Console → Hledej JS errory

# 3. Check API endpoint
curl http://localhost:8000/api/field-config/revision/all
```

---

## 📦 SOUBORY V PHASE 4

### Nové soubory k přidání:
```
✅ migrate_phase4.py
✅ seed_field_config.py
✅ templates/components/form_field_dynamic.html
✅ PHASE4-README.md
✅ PHASE4-CHANGELOG.md
✅ PHASE4-TESTING-GUIDE.md
✅ PHASE4-INSTALLATION-GUIDE.md (tento soubor)
```

### Upravené soubory:
```
✅ models.py                  (rozšířený DropdownConfig)
✅ main.py                    (nové API endpointy)
✅ templates/settings.html    (nová sekce)
```

---

## ✅ POST-INSTALLATION CHECKLIST

Po instalaci zkontroluj:

- [ ] Migrace proběhla úspěšně (6 nových sloupců)
- [ ] Seed data naplněna (76 field configs)
- [ ] Settings page zobrazuje novou sekci
- [ ] Lze vybrat entitu a zobrazit pole
- [ ] API endpointy odpovídají (test curl)
- [ ] Browser console bez errorů
- [ ] Existující funkce stále fungují (dropdown, quick add, atd.)

---

## 🎯 CO DĚLAT DÁLE

### 1. Otestuj základní funkce
```bash
# Viz PHASE4-TESTING-GUIDE.md
```

### 2. Nakonfiguruj pole podle svého workflow
```
Settings → Konfigurace viditelnosti polí
→ Vyber entitu
→ Zapni/vypni pole
→ Ulož
```

### 3. (Volitelné) Update formulářů na dynamické renderování
```python
# V každém form endpointu přidej:
field_configs = get_entity_field_config('entity_type', db)

# V template použij:
{% from 'components/form_field_dynamic.html' import render_entity_form %}
{{ render_entity_form('entity_type', field_configs, entity_obj) }}
```

---

## 🆘 POTŘEBUJEŠ POMOC?

1. **Přečti si dokumentaci:**
   - PHASE4-README.md - Kompletní info
   - PHASE4-CHANGELOG.md - Co se změnilo
   - PHASE4-TESTING-GUIDE.md - Jak testovat

2. **Check common issues:**
   - Migrace errors → Zkontroluj DB connection
   - Seed errors → Zkontroluj že migrace proběhla
   - UI errors → Check browser console
   - API errors → Test curl endpointy

3. **Rollback (pokud je potřeba):**
   ```bash
   # Restore backup
   cp revize.db.backup_phase4 revize.db
   
   # Nebo pro Railway:
   railway pg:restore backup_phase4_YYYYMMDD.sql
   ```

---

## 🎉 HOTOVO!

Po úspěšné instalaci máš:
- ✅ Konfigurovatelná pole ve formulářích
- ✅ Settings UI pro správu viditelnosti polí
- ✅ API endpointy pro field configuration
- ✅ Dynamické renderování formulářů (když použiješ macros)

**Enjoy Phase 4! 🚀**
