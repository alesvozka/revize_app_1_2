# ✅ TESTING CHECKLIST - FÁZE 2

## 🎯 QUICK TESTS (5 minut)

### Test 1: Základní Flow
- [ ] Klikni FAB (+) button
- [ ] Modal se otevře
- [ ] Vyplň "Bytový dům Praha", "Jan Novák", "Praha 1"
- [ ] Klikni "Další"
- [ ] Stepper ukázal zelený checkmark na kroku 1
- [ ] Krok 2 se načetl
- [ ] Klikni [2]
- [ ] Zobrazily se 2 formuláře pro rozváděče
- [ ] Vyplň "Hlavní rozváděč" a "Podružný rozváděč"
- [ ] Klikni "Dokončit"
- [ ] Success screen se zobrazil
- [ ] Klikni "Přejít na revizi"
- [ ] Detail revize se otevřel s 2 rozváděči

**Expected:** Vše funguje smoothly, 0 page reloads ✅

---

### Test 2: Validace
- [ ] Otevři modal
- [ ] Zkus kliknout "Další" bez vyplnění
- [ ] HTML5 validace zabrání odeslání
- [ ] Vyplň povinná pole
- [ ] Klikni "Další"
- [ ] Na kroku 2 NEPŘIDÁVEJ žádné rozváděče
- [ ] Klikni "Dokončit"
- [ ] Alert: "Přidejte alespoň jeden rozváděč!"

**Expected:** Validace funguje korektně ✅

---

### Test 3: Odstranění Rozváděče
- [ ] Otevři modal, pokračuj na Krok 2
- [ ] Klikni [3] pro přidání 3 rozváděčů
- [ ] Ověř, že vidíš "Rozváděč 1", "Rozváděč 2", "Rozváděč 3"
- [ ] Klikni [X] na "Rozváděč 2"
- [ ] Formulář by měl zmizet s animací
- [ ] Ověř, že zůstaly "Rozváděč 1" a "Rozváděč 2" (přečíslováno)

**Expected:** Odstranění a přečíslování funguje ✅

---

### Test 4: Collapsible Více Polí
- [ ] Otevři modal
- [ ] Klikni "Více polí (volitelné)"
- [ ] Sekce se rozbalí
- [ ] Vyplň "Kód revize: R-2025-001"
- [ ] Vyplň "Datum kontroly: dnes"
- [ ] Vyber "Typ revize: Pravidelná"
- [ ] Vyplň "Technik: Petr Svoboda"
- [ ] Klikni "Další" a dokončit flow
- [ ] Po vytvoření, přejdi na detail revize
- [ ] Ověř, že všechny dodatečné údaje jsou uloženy

**Expected:** Optional pole fungují ✅

---

### Test 5: ESC & Backdrop Click
- [ ] Otevři modal
- [ ] Stiskni ESC
- [ ] Modal by se měl zavřít
- [ ] Otevři znovu
- [ ] Klikni MIMO modal (na šedivou overlay)
- [ ] Modal by se měl zavřít
- [ ] Otevři znovu
- [ ] Klikni [X] v pravém horním rohu
- [ ] Modal by se měl zavřít

**Expected:** Všechny způsoby zavření fungují ✅

---

## 📱 MOBILE TESTS (10 minut)

### Test 6: Mobile Responsivita
- [ ] Otevři Chrome DevTools (F12)
- [ ] Toggle device toolbar (Ctrl+Shift+M)
- [ ] Nastav na iPhone SE (375px)
- [ ] Otevři modal
- [ ] Ověř, že modal zabírá celou šířku (minus 16px padding)
- [ ] Ověř, že všechny buttony jsou ≥44px výšky
- [ ] Zkus scrollovat uvnitř modalu
- [ ] Modal body by měl scrollovat, ne celá stránka

**Expected:** Mobile UI je použitelné ✅

---

### Test 7: iOS Zoom Prevention
- [ ] V mobile view, klikni na input "Název revize"
- [ ] Input se zfokusuje
- [ ] Ověř, že stránka NEZOOMOVALA
- [ ] (Font-size by měl být 16px, ne 14px)

**Expected:** Žádný zoom na iOS ✅

---

### Test 8: Touch Targets
- [ ] V mobile view
- [ ] Zkus tapnout na všechny buttony
- [ ] Quick buttons [1][2][3][5][10]
- [ ] [+ Přidat další]
- [ ] [X] odstranit rozváděč
- [ ] [Zpět] [Dokončit]
- [ ] Všechny by měly reagovat smoothly

**Expected:** Touch feedback je okamžitý ✅

---

## 🔧 EDGE CASES (5 minut)

### Test 9: 10+ Rozváděčů
- [ ] Otevři modal, pokračuj na Krok 2
- [ ] Klikni [10]
- [ ] Ověř, že se zobrazilo 10 formulářů
- [ ] Scroll by měl fungovat
- [ ] Vyplň všech 10 názvů
- [ ] Dokončit
- [ ] Success screen ukáže "10 rozváděčů vytvořeno"

**Expected:** Zvládá velké množství rozváděčů ✅

---

### Test 10: Prázdný Typ Rozváděče
- [ ] Otevři modal, pokračuj na Krok 2
- [ ] Přidej 1 rozváděč
- [ ] Vyplň POUZE název
- [ ] NECH dropdown "Typ" prázdný (-- Volitelné --)
- [ ] Dokončit
- [ ] Ověř v detailu revize, že rozváděč má název, ale NEmá typ

**Expected:** Optional pole zůstává optional ✅

---

### Test 11: Zpět na Krok 1
- [ ] Otevři modal
- [ ] Vyplň krok 1
- [ ] Klikni "Další"
- [ ] Na kroku 2, klikni "Zpět"
- [ ] Vrátil ses na krok 1
- [ ] Stepper se vrátil (modrý na kroku 1)
- [ ] Data z kroku 1 NEJSOU předvyplněná (to je OK)

**Expected:** Zpět funguje ✅

---

## 🎨 VISUAL TESTS (5 minut)

### Test 12: Animace
- [ ] Otevři modal → fade in animace
- [ ] Přejdi na krok 2 → smooth transition
- [ ] Přidej rozváděč → auto-focus na input
- [ ] Odstraň rozváděč → fade out animace
- [ ] Success screen → bounce animace na checkmark

**Expected:** Všechny animace smooth ✅

---

### Test 13: Stepper State
- [ ] Krok 1: Kroužek 1 = modrý, Kroužek 2 = šedý
- [ ] Krok 2: Kroužek 1 = zelený (✓), Kroužek 2 = modrý
- [ ] Label barvy odpovídají stavu kroužků

**Expected:** Stepper vizuálně správný ✅

---

## 🐛 ERROR HANDLING (5 minut)

### Test 14: Databázová Chyba (simulace)
- [ ] V main.py, dočasně přidej `raise Exception("Test error")` do `quick_entry_complete`
- [ ] Zkus vytvořit revizi
- [ ] Měla by se zobrazit červená error zpráva
- [ ] Odstraň test error
- [ ] Zkus znovu → nyní by mělo fungovat

**Expected:** Chyby jsou zachyceny a zobrazeny ✅

---

## 📊 RESULTS

**Total Tests:** 14  
**Passed:** ___  
**Failed:** ___  
**Skipped:** ___

---

## 🎯 KRITICKÁ KRITÉRIA

Aby byla Fáze 2 hotová, musí projít:
- ✅ Test 1 (Základní Flow)
- ✅ Test 2 (Validace)
- ✅ Test 5 (ESC & Backdrop)
- ✅ Test 6 (Mobile Responsivita)

**Status:** ☐ READY FOR PRODUCTION

---

## 📝 NOTES

Zapiš si zde jakékoliv problémy nebo postřehy během testování:

```
[Zde tvoje poznámky]
```
