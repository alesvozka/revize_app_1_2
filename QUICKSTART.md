# 🚀 QUICK START GUIDE - FÁZE 2

## ⚡ 60 SEKUND DO SPUŠTĚNÍ

### 1. Rozbal archiv
```bash
tar -xzf revize-app-phase2-complete.tar.gz
cd revize-app-phase2-complete
```

### 2. Spusť aplikaci
```bash
python main.py
```

### 3. Otevři prohlížeč
```
http://localhost:8000
```

### 4. Vyzkoušej Quick Entry
1. Klikni na **FAB (+) button** dole uprostřed
2. Vyplň formulář:
   - Název: `Test Revize`
   - Klient: `Test Klient`
   - Adresa: `Test Adresa`
3. Klikni **Další →**
4. Klikni **[2]** pro přidání 2 rozváděčů
5. Vyplň názvy rozváděčů
6. Klikni **Dokončit ✓**

**🎉 HOTOVO!** Revize s 2 rozváděči vytvořena za ~30 sekund!

---

## 📋 CO JE NOVÉHO

### ✨ Quick Entry Modal
- **Krok 1:** Základní info (Název, Klient, Adresa + více volitelných polí)
- **Krok 2:** Quick add rozváděčů ([1][2][3][5][10] buttons)
- **Krok 3:** Success screen s odkazem na revizi

### ⚡ Rychlost
- **Před:** 29+ kliků, 29 page loads
- **Nyní:** ~12 kliků, 0 page loads
- **Úspora:** ~70% času! ⚡

---

## 🎯 HLAVNÍ FEATURES

### Quick Buttons
Kliknutím na číslo vytvoříš tolik prázdných formulářů:
- [1] → 1 rozváděč
- [2] → 2 rozváděče
- [3] → 3 rozváděče
- [5] → 5 rozváděčů
- [10] → 10 rozváděčů

### + Přidat další
Postupné přidávání po jednom rozváděči

### X Odstranit
Každý rozváděč má [X] button pro smazání

### Více polí
Collapsible sekce s volitelnými poli:
- Kód revize
- Datum kontroly
- Typ revize
- Technik
- Popis

---

## 📱 MOBILE OPTIMALIZACE

- ✅ Touch targets ≥44px
- ✅ Font-size 16px (iOS zoom prevention)
- ✅ Responsive design
- ✅ Smooth animations

---

## ⌨️ KEYBOARD SHORTCUTS

- **ESC** → Zavřít modal
- **Enter** → Odeslat formulář
- **Tab** → Navigace mezi poli

---

## 🐛 TROUBLESHOOTING

### Modal se neotevírá?
1. Otevři konzoli (F12)
2. Zkontroluj chyby
3. Ověř, že HTMX je načtený

### Dropdown typy rozváděčů je prázdný?
- Normální! Typy se načítají z databáze
- Pokud dropdown není enabled v Nastavení → zůstane prázdný
- Můžeš přidat typy v Nastavení

### Session data chybí?
- Session se vyčistí po restartu serveru
- To je OK, je to temporary data

---

## 📚 DALŠÍ DOKUMENTACE

- **PHASE2-README.md** → Kompletní dokumentace
- **TESTING-CHECKLIST.md** → Testing checklist

---

## 🎉 ENJOY!

Máš otázky? Narazil jsi na problém?
- Zkontroluj konzoli (F12)
- Zkontroluj server logs
- Přečti si PHASE2-README.md

**Happy coding! 🚀**
