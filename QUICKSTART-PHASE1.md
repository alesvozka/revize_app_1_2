# 🚀 QUICK START - Fáze 1 Testing

## ⚡ 3 MINUTY DO TESTOVÁNÍ

### 1. Spuštění (30 sekund)
```bash
cd revize-app-redesign
python main.py
```

### 2. Otevři prohlížeč (10 sekund)
```
http://localhost:8000
```

### 3. Testuj Mobile View (30 sekund)
**Chrome/Edge:**
1. Stiskni `F12` (otevře DevTools)
2. Stiskni `Ctrl+Shift+M` (Device Toolbar)
3. Vyber "iPhone 12 Pro" nebo "Pixel 5"

**Firefox:**
1. Stiskni `F12`
2. Klikni na ikonu mobilu vlevo nahoře
3. Vyber "iPhone 12/13 Pro"

---

## ✅ CO VYZKOUŠET (2 minuty)

### Test #1: Bottom Navigation
1. **Zmenši okno** na mobilní velikost
2. **Podívej se dolů** - měl by být vidět bottom nav s 5 ikonami
3. **Klikni na FAB (+)** uprostřed → měl by se zobrazit alert
4. **Klikni na ikony** vlevo a vpravo → přejde na stránky

✅ **Expected:** Bottom nav je fixní dole, FAB je zvýrazněný, aktivní ikona je modrá

---

### Test #2: Breadcrumb
1. **Klikni na nějakou revizi** z dashboardu
2. **Nahoře by měl být breadcrumb** s: `Dashboard > Revize XYZ`
3. **Klikni na rozváděč**
4. **Breadcrumb by měl ukazovat:** `Dashboard > Revize XYZ > Rozváděč ABC`

✅ **Expected:** Breadcrumb je sticky (zůstává nahoře při scrollování)

---

### Test #3: Profile Page
1. **Klikni na ikonu profilu** (úplně vpravo v bottom nav)
2. **Měl by se zobrazit profil** se statistikami
3. **Měly by být vidět karty:** Revize / Rozváděče / Přístroje

✅ **Expected:** Statistiky odpovídají tvým datům

---

### Test #4: Touch Targets
1. **Zkus kliknout na různá tlačítka**
2. **Všechna by měla být dostatečně velká** (44x44px minimum)
3. **FAB button by měl mít hover effect** (zvětší se)

✅ **Expected:** Žádné problémy s klikáním na mobilech

---

## 🎯 RYCHLÁ NAVIGACE

```
/                  → Dashboard
/profile           → Profil (nový!)
/settings          → Nastavení
/revision/create   → Nová revize
/revision/[id]     → Detail revize (má breadcrumb)
/switchboard/[id]  → Detail rozváděče (má breadcrumb)
```

---

## 📱 TEST NA SKUTEČNÉM MOBILU

### Zjisti IP svého počítače:

**Windows:**
```bash
ipconfig
# Najdi "IPv4 Address" - např. 192.168.1.100
```

**Mac/Linux:**
```bash
ifconfig | grep inet
# Najdi lokální IP - např. 192.168.1.100
```

### Na mobilu otevři:
```
http://[TVOJE-IP]:8000
```
Např: `http://192.168.1.100:8000`

⚠️ **Pozor:** Mobil a počítač musí být na stejné WiFi síti!

---

## ❌ KDYŽ NĚCO NEFUNGUJE

### Bottom nav není viditelný?
- ✅ Zkontroluj že máš okno zmenšené na mobilní velikost
- ✅ Hard refresh: `Ctrl+Shift+R` nebo `Cmd+Shift+R`

### FAB button nedělá nic?
- ✅ Měl by zobrazit alert s textem o Fázi 2
- ✅ Pokud ne, zkontroluj JavaScript Console (F12)

### Breadcrumb se nezobrazuje?
- ✅ Funguje pouze na `revision_detail.html` a `switchboard_detail.html`
- ✅ Na ostatních stránkách musíš přidat `{% set breadcrumbs = [...] %}`

### Profile stránka vrací 404?
- ✅ Ujisti se že máš aktuální `main.py` s `/profile` endpointem
- ✅ Restartuj server

---

## 🎉 KDYŽ VŠE FUNGUJE

**Gratulujeme! Fáze 1 je úspěšně implementována!** 🎊

Aplikace má nyní:
- ✅ Professional mobile navigation
- ✅ FAB button připravený pro Quick Entry
- ✅ Breadcrumb systém
- ✅ Mobile-first optimalizace
- ✅ Profile stránku

**Připraven na Fázi 2?** 🚀

Následující krok je **Quick Entry Modal** - multi-step formulář pro rychlé založení revize s minimem kliků!

---

**Happy testing! 🧪**
