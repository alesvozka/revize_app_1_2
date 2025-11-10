# 🔍 KROK ZA KROKEM - DIAGNOSTIKA DROPDOWN PROBLÉMU

## 🎯 Cíl
Zjistit, proč se dropdowny nezobrazují ve formulářích, i když jsou v nastavení zapnuté.

## 📋 Příprava
1. Stáhni a rozbal opravenou aplikaci
2. Ujisti se, že máš aktivní databázové připojení
3. Otevři terminál v adresáři aplikace

## 🚀 KROK 1: Spusť kompletní diagnostiku

```bash
python run_diagnostics.py
```

Tento script spustí 4 diagnostické kontroly najednou a ukáže ti kompletní přehled.

**Co kontroluje:**
- ✅ Co je v databázi (DropdownConfig tabulka)
- ✅ Jaké kategorie a hodnoty existují (DropdownSource)
- ✅ Co vrací funkce `get_entity_field_config()`
- ✅ Která pole mají dropdown, ale jsou skrytá

---

## 🔍 KROK 2: Analyzuj výsledky

### Scénář A: Pole jsou SKRYTÁ
```
⚠️  X polí má zapnutý dropdown, ale pole NENÍ VIDITELNÉ!
```

**Řešení:** Spusť automatickou opravu:
```bash
python fix_dropdown_visibility.py
```

---

### Scénář B: Chybí KATEGORIE nebo HODNOTY
```
❌ X categories are configured but have NO values:
   - 'typ_revize' (used by 1 field(s))
```

**Řešení:** 
1. Otevři aplikaci: http://localhost:8000/settings
2. Záložka "🗂️ Správa dropdown hodnot"
3. Přidej kategorii "typ_revize" (pokud neexistuje)
4. Přidej hodnoty do kategorie (např. "Výchozí", "Periodická", "Mimořádná")

---

### Scénář C: Pole MA dropdown, ALE kategorie je ŠPATNÁ
Ze screenshotů vidím:
- "Klient" má kategorii "celkove_hodnoceni" ❌
- "Celkové hodnocení" má kategorii "celkove_hodnoceni" ❌

**Problém:** Obě pole používají STEJNOU kategorii! To je chyba.

**Řešení:**
1. Otevři /settings
2. Záložka "🔽 Dropdown konfigurace"
3. Pro pole "Klient":
   - Změň kategorii z "celkove_hodnoceni" na správnou (např. "klienti" nebo "firmy")
   - Klikni "💾 Uložit"
4. Pro pole "Celkové hodnocení":
   - Nech kategorii "celkove_hodnoceni"
   - Nebo změň na "hodnoceni"

---

## 🧪 KROK 3: Test ve webové aplikaci

### A) Zkontroluj nastavení
1. Otevři http://localhost:8000/settings
2. Záložka "👁️ Viditelnost polí" - **musí být ZAPNUTÁ** ✅
3. Záložka "🔽 Dropdown konfigurace":
   - Checkbox zaškrtnutý ✅
   - Kategorie vybraná (ne "-- Vyberte kategorii --") ✅
   - Kliknuté "💾 Uložit" ✅

### B) Otevři formulář
1. Vytvoř novou revizi: http://localhost:8000/revision/create
2. **Kontrola:** U pole s dropdownem by mělo být:
   - ✅ Input pole (můžeš psát přímo)
   - ✅ Šipka vpravo (tlačítko pro dropdown)
   - ✅ Po kliknutí na šipku se otevře dropdown menu
   - ✅ V dropdownu jsou hodnoty z databáze
   - ✅ Možnost "Přidat novou hodnotu..."

### C) Debug v prohlížeči
Pokud se widget stále nezobrazuje:
1. Otevři Developer Tools (F12)
2. Zkontroluj HTML source (View Page Source)
3. Hledej komentáře:
   ```html
   <!-- DEBUG FIELD: revision_type | has_dropdown=True | dropdown_category=typ_revize -->
   <!-- DEBUG: Rendering dropdown widget for revision_type with category typ_revize -->
   ```
4. Pokud vidíš:
   ```html
   <!-- DEBUG: Rendering standard input for revision_type (has_dropdown=False, dropdown_category=None) -->
   ```
   → Problém je v databázi nebo v `get_entity_field_config()`

---

## 📊 KROK 4: Kontrola v console logu

Když spustíš aplikaci, měl bys vidět debug výpisy:
```
🔍 DEBUG get_entity_field_config(revision): 8 viditelných polí, 3 s dropdownem
  - revision_type: dropdown ✅ kategorie: typ_revize
  - revision_client: dropdown ✅ kategorie: klienti
```

Pokud vidíš:
```
🔍 DEBUG get_entity_field_config(revision): 8 viditelných polí, 0 s dropdownem
```
→ Žádné pole nemá `dropdown_enabled=True` nebo `dropdown_category`!

---

## 🐛 NEJČASTĚJŠÍ PROBLÉMY

### 1. Pole skryté (enabled=False)
**Symptom:** V nastavení je checkbox dropdown zaškrtnutý, ale pole není ve formuláři  
**Řešení:** `python fix_dropdown_visibility.py`

### 2. Chybí kategorie
**Symptom:** Widget se zobrazí, ale v dropdownu je "Žádné hodnoty v kategorii..."  
**Řešení:** Přidej hodnoty do kategorie v /settings

### 3. Špatná kategorie
**Symptom:** Dropdown má hodnoty, ale nejsou relevantní  
**Řešení:** Změň kategorii v nastavení

### 4. Podmínka False
**Symptom:** V HTML source jsou jen standard inputy  
**Řešení:** Zkontroluj v databázi: `python check_database.py`

---

## 💡 PRO TIP

Pokud chceš rychle vidět, co je špatně, spusť:
```bash
python check_dropdowns.py
```

Ten ti ukáže přesně, která pole mají problém a proč.

---

## 📞 Pokud nic nepomůže

Pošli mi:
1. Výstup z `python run_diagnostics.py`
2. Screenshot z /settings (obě záložky)
3. Screenshot HTML source z formuláře (View Page Source)
4. Console log z aplikace (když se načítá formulář)

---

**Vytvořeno:** 2025-11-10  
**Verze:** 1.0 - Complete Diagnostic
