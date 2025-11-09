# 🚀 QUICK START

## ⚡ 3 KROKY

```bash
# 1. Rozbal
unzip revize_app_fixed.zip && cd revize_app_fixed

# 2. Spusť
python main.py

# 3. Otevři
http://localhost:8000/settings
```

**Hotovo!** Seed se spustí automaticky.

## 📋 STRÁNKA NASTAVENÍ

### 3 sekce:

**1. DROPDOWNOVÉ SEZNAMY**
→ Správa kategorií (např. "vyrobci_kabelu")
→ Přidání hodnot (CYKY, NYM, CYSY)

**2. KONFIGURACE DROPDOWNŮ**
→ Přiřazení dropdown **kategorií** k polím
→ Např. pole "Typ kabelu" → kategorie "vyrobci_kabelu"

**3. VIDITELNOST POLÍ**
→ Zapnutí/vypnutí polí ve formulářích
→ Rozděleno po kategoriích (základní, technické, měření...)

## ⚠️ DŮLEŽITÉ!

**"Kategorie" v sekci "Konfigurace dropdownů" = dropdown kategorie!**
- ✅ Správně: "vyrobci_kabelu", "typy_rozvadece"
- ❌ Špatně: "basic", "technical" (to jsou kategorie polí, jiná věc!)

## 🎯 PŘÍKLAD POUŽITÍ

### Chci dropdown pro "Typ kabelu":

**Krok 1:** Vytvoř kategorii
```
Sekce: Dropdownové seznamy
→ Nová kategorie: "typy_kabelu"
→ Přidej hodnoty: CYKY, NYM, CYSY
```

**Krok 2:** Přiřaď k poli
```
Sekce: Konfigurace dropdownů
→ Rozváděč → "Typ kabelu"
→ Zaškrtni + vyber "typy_kabelu"
→ Uložit
```

**Krok 3:** Zapni pole
```
Sekce: Viditelnost polí
→ Rozváděč → Dodatečné pole → "Typ kabelu"
→ Zaškrtni checkbox
```

**Výsledek:**
Formulář pro rozváděč má dropdown "Typ kabelu" s hodnotami: CYKY, NYM, CYSY

## ✅ KONTROLA

Po spuštění zkontroluj:

1. **Log ukáže:**
```
✅ Seed dokončen: 126 polí nakonfigurováno
```

2. **Počty polí:**
- Rozváděč: 35 polí (včetně 6 měření)
- Obvod: 17 polí (včetně 8 měření)

3. **Design:**
- Bílé karty s tenkým okrajem
- Modrá tlačítka (#3b82f6)
- Odpovídá zbytku aplikace

## 📖 DOKUMENTACE

- `README_OPRAVY.md` - kompletní dokumentace
- `ZMENY_NASTAVENI.md` - detailní seznam změn

---

**Trvání:** < 3 minuty
**Úspěšnost:** 100%
