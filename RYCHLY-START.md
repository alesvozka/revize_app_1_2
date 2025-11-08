# ⚡ RYCHLÝ START - Kompaktní Dropdown

## 🎯 Co nahradit

Nahraď **pouze 2 soubory**:

```
✅ templates/components/form_field.html
✅ templates/base.html
```

## 📋 Checklist nasazení

### 1. Backup (volitelné, ale doporučené)
- [ ] Zálohuj `templates/components/form_field.html`
- [ ] Zálohuj `templates/base.html`

### 2. Nahrání souborů
- [ ] Nahraj nový `form_field.html` do `templates/components/`
- [ ] Nahraj nový `base.html` do `templates/`

### 3. Restart
- [ ] Railway automaticky restartuje
- [ ] Počkej 30-60 sekund na restart

### 4. Test v prohlížeči
- [ ] Otevři aplikaci
- [ ] Hard refresh: **Ctrl + F5** (Windows) nebo **Cmd + Shift + R** (Mac)
- [ ] Otevři formulář (např. Nový rozváděč)
- [ ] Najdi pole s dropdownem

### 5. Ověř funkčnost
- [ ] **Vidím kompaktní pole** (input + šipka vpravo)
- [ ] **Klik na šipku** → otevře dropdown
- [ ] **Vyber hodnotu** → zavře se a vyplní
- [ ] **Klik "➕ Přidat novou"** → otevře modal
- [ ] **Zadej hodnotu v modalu** → uloží a vybere

## ✅ Co očekávat

### PŘED:
```
[📋 Databáze] [➕ Nový] [✎ Text]  ← 3 tlačítka
┌────────────────────────────┐
│ -- Vyberte hodnotu --    ▼│    ← Systémový select
└────────────────────────────┘
```

### PO:
```
┌────────────────────────┬──┐
│ Vyberte nebo zadejte...│▼│    ← Kompaktní combo box
└────────────────────────┴──┘
💡 Pište přímo nebo klikněte na šipku
```

## 🐛 Něco nefunguje?

### Stále vidím systémové selecty?
1. Hard refresh: **Ctrl + F5**
2. Zkontroluj, že jsi nahrál do správné složky
3. Otevři konzoli (F12) - jsou chyby?

### Dropdown se neotevírá?
1. Zkontroluj, že jsi nahrál `base.html`
2. Otevři konzoli (F12) - jsou chyby JavaScriptu?
3. Zkus jinou stránku (cache problém)

### Modal se neotevírá?
1. Konzole (F12) → zkontroluj chyby
2. Ověř, že `base.html` obsahuje modal element

## 📞 Potřebuješ pomoc?

Pošli mi:
- ✅ Screenshot toho, co vidíš
- ✅ Screenshot konzole (F12)
- ✅ URL stránky kde testuješ

---

**Celý proces by měl trvat 2-3 minuty!** ⚡
