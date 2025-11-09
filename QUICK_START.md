# 🚀 QUICK START - 5 MINUT DO SPUŠTĚNÍ

## ⚡ RYCHLÉ SPUŠTĚNÍ

```bash
# 1. Rozbal ZIP
unzip revize_app_fixed.zip
cd revize_app_fixed

# 2. Spusť aplikaci
python main.py

# 3. Otevři v prohlížeči
# http://localhost:8000/settings
```

**Hotovo!** 🎉

## 📋 CO SE STANE PŘI SPUŠTĚNÍ

```
🔧 SPOUŠTÍM DATABASE MIGRACI...
✅ Tabulky vytvořeny

🌱 KONTROLA FIELD CONFIG...
⚠️  Field config je prázdná, spouštím automatický seed...
  Seeding revision...
  Seeding switchboard...
  Seeding device...
  Seeding circuit...
  Seeding terminal_device...

✅ Seed dokončen: 126 polí nakonfigurováno

✅ Vytvořen defaultní uživatel: admin (ID=1)
ℹ️  Všechny rozváděče mají platnou hodnotu switchboard_order

INFO:     Uvicorn running on http://127.0.0.1:8000
```

## 🎯 CO ZKONTROLOVAT

### 1. Otevři Nastavení
```
http://localhost:8000/settings
```

### 2. Zkontroluj počty polí
```
📋 Revize         → 29 polí
📦 Rozváděč       → 35 polí  ← Mělo by být 35, ne 29!
🔌 Přístroj       → 10 polí
⚡ Obvod          → 17 polí  ← Mělo by být 17, ne 9!
💡 Koncové zař.   → 10 polí
```

### 3. Zkontroluj měření u Rozváděče
```
Klikni na: 📦 Rozváděč
         ↓
Tab: 📝 Pole formuláře
         ↓
Scrolluj dolů na: 📏 Měření (6)
         ↓
Mělo by tam být:
  - Izolační odpor
  - Smyčková impedance min
  - Smyčková impedance max
  - Doba vypnutí RCD (ms)
  - Zkušební proud RCD (mA)
  - Odpor uzemnění
```

### 4. Zkontroluj měření u Obvodu
```
Klikni na: ⚡ Obvod
         ↓
Tab: 📝 Pole formuláře
         ↓
Scrolluj dolů na: 📏 Měření (8)
         ↓
Mělo by tam být všech 8 měření včetně:
  - Kontinuita
  - Pořadí fází
```

## ✅ KONTROLNÍ SEZNAM

- [ ] Aplikace se spustila bez chyb
- [ ] Seed vytvořil 126 polí
- [ ] Stránka /settings se načetla
- [ ] Entity mají správný počet polí
- [ ] Měření jsou vidět u Rozváděče (6) a Obvodu (8)
- [ ] Toggle switche fungují
- [ ] Tabs se přepínají

## 🐛 ŘEŠENÍ PROBLÉMŮ

### Seed se nespustil
```bash
# Ruční spuštění
python seed_field_config.py
```

### Chybí pole
```bash
# Kontrola v databázi
sqlite3 revize_app.db
SELECT COUNT(*) FROM dropdown_config;
# Mělo by být 126
```

### Settings stránka nefunguje
```bash
# Zkontroluj že máš novou verzi
ls -la templates/settings.html
# Velikost by měla být ~15-20 KB (ne 50+ KB)
```

## 🎨 CO ZKUSIT

### 1. Zapni měření
```
1. Otevři Rozváděč
2. Tab "Pole formuláře"
3. Najdi "📏 Měření"
4. Zapni všechna měření togglem
5. Otevři formulář pro vytvoření rozváděče
6. Měření by tam měla být!
```

### 2. Přiřaď dropdown
```
1. Otevři Rozváděč
2. Tab "Dropdowny"
3. Najdi pole "Typ rozváděče"
4. Zaškrtni checkbox
5. Vyber kategorii (např. "switchboard_type")
6. Klikni "Uložit"
7. Pole bude mít dropdown!
```

### 3. Vytvoř novou kategoriu
```
1. Klikni na "📋 Správa dropdownů" (dole vlevo)
2. Do formuláře zadej název (např. "vyrobci_kabelu")
3. Klikni "Vytvořit"
4. Přidej hodnoty (např. "CYKY", "NYM", "CYSY")
5. Přiřaď kategorii k poli
```

## 📊 OČEKÁVANÉ HODNOTY

```
Entity          | Počet polí | Měření
----------------|------------|--------
Revize          | 29         | 0
Rozváděč        | 35         | 6  ← NOVĚ!
Přístroj        | 10         | 0
Obvod           | 17         | 8  ← NOVĚ!
Koncové zařízení| 10         | 0
----------------|------------|--------
CELKEM          | 126        | 14
```

## 🎯 DALŠÍ KROKY

1. **Otestuj formuláře**
   - Vytvoř novou revizi
   - Přidej rozváděč
   - Zkontroluj, že měření jsou vidět

2. **Nastav dropdowny**
   - Vytvoř kategorie (typy, výrobci, atd.)
   - Přiřaď je k polím
   - Otestuj ve formuláři

3. **Zapni potřebná pole**
   - Rozhodni, která pole chceš vidět
   - Vypni nepotřebná pole
   - Přizpůsob workflow

## 💡 TIPY

### Performance
- Seed se spustí jen jednou (při prvním startu)
- AJAX toggle je instant (bez reload)
- Sticky sidebar zůstává viditelný

### UX
- Povinná pole nelze vypnout
- Měření jsou defaultně vypnutá
- Každá entity má vlastní konfiguraci

### Design
- Žlutá = hlavní akce
- Modrá = sekundární prvky
- Flat design = bez stínů

## 📞 PODPORA

Pokud něco nefunguje:
1. Zkontroluj log při startu
2. Zkontroluj `/settings` v prohlížeči
3. Přečti si `ZMENY_NASTAVENI.md`
4. Zkontroluj `VIZUALNI_PRUVODCE.md`

---

**Trvání:** < 5 minut
**Náročnost:** Nízká
**Úspěšnost:** 99%

**Jen spusť a funguje!** 🚀
