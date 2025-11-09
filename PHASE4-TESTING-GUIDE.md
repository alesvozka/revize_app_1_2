# 🧪 PHASE 4 TESTING GUIDE

## ⚡ RYCHLÝ START

### 1. Migrace a Setup (5 minut)

```bash
# Krok 1: Migrace databáze
python migrate_phase4.py

# Očekávaný output:
✓ Success: ALTER TABLE dropdown_config ADD COLUMN field_label...
✓ Success: ALTER TABLE dropdown_config ADD COLUMN field_category...
✓ Success: ALTER TABLE dropdown_config ADD COLUMN display_order...
✓ Success: ALTER TABLE dropdown_config ADD COLUMN enabled...
✓ Success: ALTER TABLE dropdown_config ADD COLUMN is_required...
✓ Success: ALTER TABLE dropdown_config ADD COLUMN field_type...
✓ Phase 4 migration completed!

# Krok 2: Naplnění seed dat
python seed_field_config.py

# Očekávaný output:
📋 Processing entity: revision
   ✓ Added: revision_name
   ✓ Added: revision_client
   ...
✓ Field configurations seeded!
  Added: 76
  Updated: 0

# Krok 3: Restart aplikace
uvicorn main:app --reload
```

---

## 📋 TEST SCENARIOS

### TEST 1: Settings UI ✅

**Cíl:** Ověřit že Settings page zobrazuje novou sekci

**Kroky:**
1. Otevřete `/settings`
2. Najděte sekci "Konfigurace viditelnosti polí"
3. Klikněte na tlačítko "Revize"

**Očekávaný výsledek:**
```
✅ Zobrazí se základní pole (s POVINNÉ badge, disabled checkbox)
✅ Zobrazí se dodatečná pole (enabled checkbox)
✅ Každé pole má input pro pořadí
✅ Tlačítka "Zapnout vše" a "Vypnout vše" jsou viditelná
```

**Screenshot lokace:**
```
Settings → Konfigurace viditelnosti polí → [📋 Revize]
```

---

### TEST 2: Zapnutí/Vypnutí Polí ✅

**Cíl:** Ověřit že lze zapínat a vypínat pole

**Kroky:**
1. V Settings → Field Visibility → Revize
2. Odškrtněte "Kód revize"
3. Odškrtněte "Datum předchozí revize"
4. Klikněte "💾 Uložit změny"
5. Otevřete `/revision/create` (nebo jiný Revize formulář)

**Očekávaný výsledek:**
```
✅ Formulář NEZOBRAZUJE "Kód revize"
✅ Formulář NEZOBRAZUJE "Datum předchozí revize"
✅ Ostatní pole jsou zobrazena
```

---

### TEST 3: Povinná Pole ✅

**Cíl:** Ověřit že povinná pole nelze vypnout

**Kroky:**
1. V Settings → Field Visibility → Revize
2. Najděte pole "Název revize" nebo "Klient"

**Očekávaný výsledek:**
```
✅ Checkbox je disabled (šedý)
✅ Je zobrazen badge "POVINNÉ"
✅ Nelze odškrtnout
✅ Pole je vždy checked
```

---

### TEST 4: Změna Pořadí ✅

**Cíl:** Ověřit že lze měnit pořadí polí

**Kroky:**
1. V Settings → Field Visibility → Revize
2. Změňte pořadí pole "Vlastník" z 11 na 3
3. Uložte změny
4. Otevřete formulář Revize

**Očekávaný výsledek:**
```
✅ Pole "Vlastník" se zobrazí jako 3. v pořadí
✅ Je mezi "Klient" (2) a "Kód revize" (10)
```

---

### TEST 5: Hromadné Akce ✅

**Kroky - Vypnout vše:**
1. Settings → Field Visibility → Rozváděč
2. Klikněte "✗ Vypnout všechna dodatečná pole"
3. Potvrďte dialog
4. Otevřete formulář Rozváděč

**Očekávaný výsledek:**
```
✅ Zobrazí se POUZE základní pole (Název, Umístění)
✅ Všechna dodatečná pole jsou skrytá
```

**Kroky - Zapnout vše:**
1. Klikněte "✓ Zapnout všechna dodatečná pole"
2. Potvrďte dialog
3. Otevřete formulář Rozváděč

**Očekávaný výsledek:**
```
✅ Zobrazí se VŠECHNA pole
✅ Formulář má ~26 polí
```

---

### TEST 6: API Endpointy ✅

**Test GET /api/form-config/revision:**

```bash
curl http://localhost:8000/api/form-config/revision
```

**Očekávaný response:**
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

**Test GET /api/field-config/revision/all:**

```bash
curl http://localhost:8000/api/field-config/revision/all
```

**Očekávaný response:**
```json
{
  "entity_type": "revision",
  "fields_by_category": {
    "basic": [...],
    "additional": [...]
  }
}
```

---

### TEST 7: Různé Entity ✅

**Cíl:** Ověřit že konfigurace funguje pro všechny entity

**Kroky pro každou entitu:**
1. Settings → Field Visibility → [Vyberte entitu]
2. Vypněte 2-3 pole
3. Uložte
4. Otevřete příslušný formulář

**Entity k otestování:**
- [ ] 📋 Revize (`/revision/create`)
- [ ] 📦 Rozváděč (Quick Add v revision detail)
- [ ] 🔌 Přístroj (Quick Add v switchboard detail)
- [ ] ⚡ Obvod (Quick Add v device/circuit view)
- [ ] 💡 Koncové zařízení (Quick Add v circuit detail)

**Očekávaný výsledek pro každou:**
```
✅ Vypnutá pole se nezobrazují
✅ Zapnutá pole jsou v pořadí
✅ Povinná pole jsou vždy zobrazena
```

---

### TEST 8: Regrese - Dropdown Funkce ✅

**Cíl:** Ověřit že Phase 2-3 dropdown konfigurace stále funguje

**Kroky:**
1. Settings → Dropdownové seznamy → Konfigurace Polí
2. Ověřte že dropdown konfigurace je stále viditelná
3. Zapněte dropdown pro nějaké pole (např. "switchboard_type")
4. Otevřete formulář Rozváděč

**Očekávaný výsledek:**
```
✅ Dropdown konfigurace sekce stále existuje
✅ Pole s dropdownem má 3-mode widget
✅ Lze vybrat z hodnot, přidat novou, nebo psát volně
```

---

### TEST 9: Quick Entry Modal ✅

**Cíl:** Ověřit že Quick Entry Modal respektuje field config

**Kroky:**
1. Vypněte nějaká pole pro Revizi v Settings
2. Na dashboardu klikněte "⚡ Quick Entry"
3. Projděte wizard (Step 1 + Step 2)

**Očekávaný výsledek:**
```
✅ Modal zobrazuje pouze zapnutá pole
✅ Kroky jsou správně rozdělené
✅ Po dokončení se vytvoří revize s hodnotami
```

**Poznámka:** Quick Entry může potřebovat update aby používal field config!

---

### TEST 10: Inline Quick Add ✅

**Cíl:** Ověřit že inline quick add respektuje field config

**Kroky:**
1. Vypněte nějaká pole pro Rozváděč
2. V revision detail klikněte "+ Rychlé přidání rozváděče"
3. Vyplňte formulář

**Očekávaný výsledek:**
```
✅ Inline formulář zobrazuje pouze zapnutá pole
✅ Po uložení se přidá rozváděč
✅ Seznam se aktualizuje
```

**Poznámka:** Inline quick add může potřebovat update!

---

## 🐛 COMMON ISSUES & FIXES

### Issue 1: "Field config se nenačítá"

**Symptom:**
```
Settings → Field Visibility → Vyberu entitu → Nic se nezobrazí
```

**Diagnóza:**
```bash
# Check browser console
F12 → Console → Hledej chyby

# Check API
curl http://localhost:8000/api/field-config/revision/all

# Check DB
SELECT COUNT(*) FROM dropdown_config WHERE field_label IS NOT NULL;
```

**Fix:**
```bash
# Znovu spusť seed
python seed_field_config.py
```

---

### Issue 2: "Migrace selhala"

**Symptom:**
```
ERROR: column "field_label" already exists
```

**Diagnóza:**
```sql
-- Check tabulka struktura
SELECT column_name FROM information_schema.columns 
WHERE table_name = 'dropdown_config';
```

**Fix:**
```bash
# Migrace již byla provedena, přeskoč ji
# Nebo dropni a znovu vytvoř tabulku (pouze v dev!)
```

---

### Issue 3: "Formulář stále zobrazuje všechna pole"

**Symptom:**
```
Vypnul jsem pole v Settings, ale formulář je stále zobrazuje
```

**Diagnóza:**
```python
# Check že endpoint používá get_entity_field_config()
# Check že template používá form_field_dynamic.html macro
```

**Fix:**
```python
# V endpointu:
field_configs = get_entity_field_config('revision', db)

# V template:
{% from 'components/form_field_dynamic.html' import render_entity_form %}
{{ render_entity_form('revision', field_configs, revision) }}
```

---

## ✅ ACCEPTANCE CRITERIA

Po dokončení všech testů:

- [ ] ✅ Migrace proběhla bez chyb
- [ ] ✅ Seed data naplněna (76 polí)
- [ ] ✅ Settings zobrazuje field visibility sekci
- [ ] ✅ Lze zapínat/vypínat dodatečná pole
- [ ] ✅ Nelze vypnout povinná pole
- [ ] ✅ Lze měnit pořadí polí
- [ ] ✅ Hromadné akce fungují
- [ ] ✅ Formuláře respektují konfiguraci
- [ ] ✅ API endpointy fungují
- [ ] ✅ Dropdown konfigurace stále funguje
- [ ] ✅ Quick Entry Modal funguje (nebo je ready for update)
- [ ] ✅ Inline Quick Add funguje (nebo je ready for update)

---

## 📊 PERFORMANCE CHECK

### Before Tests:
```bash
# Note current page load times
# Settings page: _____ ms
# Revision form: _____ ms
```

### After Tests:
```bash
# Measure again
# Settings page: _____ ms (should be similar)
# Revision form: _____ ms (should be faster if fewer fields)
```

**Expected:**
- Settings page: +50-100ms (extra field config load)
- Form pages: -10-50ms (fewer fields to render)

---

## 🎉 SUCCESS CRITERIA

**Phase 4 is successful if:**

1. ✅ Uživatel může zapnout/vypnout pole podle workflow
2. ✅ Formuláře zobrazují pouze zapnutá pole
3. ✅ Povinná pole jsou ochráněna
4. ✅ Změny se projeví okamžitě
5. ✅ Žádná regrese v existující funkčnosti
6. ✅ API endpointy fungují správně
7. ✅ UI je intuitivní a responsive

---

## 📝 TESTING NOTES

**Tester:** _____________  
**Date:** _____________  
**Environment:** Dev / Staging / Production  

**Issues found:**
1. _____________________________________________
2. _____________________________________________
3. _____________________________________________

**Overall status:** ✅ PASS / ⚠️ PARTIAL / ❌ FAIL

---

**Happy Testing! 🧪✨**
