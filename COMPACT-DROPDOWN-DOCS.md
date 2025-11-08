# Kompaktní Dropdown Widget - Dokumentace

## Přehled

Nová elegantní verze dropdown widgetu, která kombinuje všechny 3 funkce do jednoho kompaktního combo boxu.

## Porovnání verzí

### ❌ PŘED (3 tlačítka + režimy)
```
[📋 Z databáze] [➕ Přidat nový] [✎ Volný text]
┌─────────────────────────┐
│ Select dropdown         │
└─────────────────────────┘
```

### ✅ PO (Compact combo box)
```
┌─────────────────────────┬──┐
│ Zadejte hodnotu...      │▼│
└─────────────────────────┴──┘
```

## Jak to funguje

### 1. **Psaní přímo do pole**
- Uživatel píše přímo → jednorázová hodnota
- Neuloží se do databáze dropdownů
- Uloží se jen do entity
- ≈ Původní "režim 3 - Volný text"

### 2. **Kliknutí na šipku → Dropdown**
- Otevře se seznam hodnot z databáze
- Výběr hodnoty → zavře se a vyplní
- ≈ Původní "režim 1 - Z databáze"

### 3. **Poslední položka: "➕ Přidat novou hodnotu..."**
- Kliknutí otevře modal
- Zadání hodnoty → uloží se do DB (API call)
- Modal se zavře
- Dropdown se automaticky aktualizuje
- Nová hodnota se automaticky vybere
- ≈ Původní "režim 2 - Přidat nový"

## Výhody

✅ **Kompaktnější** - Méně vizuálního šumu  
✅ **Intuitivnější** - Jasné použití bez vysvětlování  
✅ **Modernější** - Běžný pattern z moderních aplikací  
✅ **Efektivnější** - Méně klikání pro běžné použití  
✅ **Zachována funkcionalita** - Všechny 3 režimy stále fungují  

## Technické detaily

### Komponenta
- **Soubor:** `templates/components/dropdown_widget_compact.html`
- **Input field:** Editovatelný pro přímé psaní
- **Dropdown button:** Šipka vpravo pro otevření seznamu
- **Modal:** Sdílený mezi všemi dropdowny na stránce
- **API:** Stejný endpoint `/api/dropdown/{category}/add`

### Parametry (nezměněné)
```python
- field_name: str       # Název pole
- field_label: str      # Label pole
- category: str         # Kategorie z dropdown_sources
- current_value: str    # Aktuální hodnota (optional)
- placeholder: str      # Placeholder text (optional)
- field_help: str       # Help text (optional)
```

### Klíčové funkce JavaScript
```javascript
toggleDropdown(fieldName)              // Otevře/zavře dropdown
selectDropdownValue(fieldName, value)  // Vybere hodnotu z DB
openAddValueModal(fieldName, category) // Otevře modal
closeAddValueModal()                   // Zavře modal
saveNewValue()                         // Uloží novou hodnotu do DB
```

## UX Vylepšení

### Animace
- ✨ Fade in pro modal overlay
- ✨ Slide up pro modal content
- ✨ Rotace šipky při otevření dropdownu
- ✨ Hover efekty na položkách

### Klávesové zkratky
- **Enter** v modalu → Uloží hodnotu
- **Escape** → Zavře modal
- **Click outside** → Zavře dropdown

### Vizuální feedback
- Zvýraznění vybrané hodnoty v dropdownu
- Zelená barva pro "Přidat novou hodnotu"
- Separator oddělující DB hodnoty od "Přidat nový"

## Zpětná kompatibilita

### Co zůstává stejné:
✅ Backend API endpointy  
✅ Parametry komponenty  
✅ Databázové schéma  
✅ Logika ukládání hodnot  
✅ Kategorie z `dropdown_sources`  

### Co se mění:
❌ UI layout (3 tlačítka → 1 combo box)  
❌ Způsob aktivace režimů (automatický → manuální)  

## Instalace

### Varianta A: Nahradit původní widget
```bash
# Zálohovat původní
mv dropdown_widget.html dropdown_widget_old.html

# Přejmenovat nový
mv dropdown_widget_compact.html dropdown_widget.html
```

### Varianta B: Použít vedle sebe
```jinja
{# Původní verze #}
{% set widget_file = 'components/dropdown_widget.html' %}

{# Kompaktní verze #}
{% set widget_file = 'components/dropdown_widget_compact.html' %}

{% include widget_file with context %}
```

## Testování

### Checklist:
- [ ] Psaní přímo do pole funguje
- [ ] Kliknutí na šipku otevře dropdown
- [ ] Výběr hodnoty z dropdownu funguje
- [ ] Poslední položka otevře modal
- [ ] Uložení nové hodnoty funguje (API call)
- [ ] Dropdown se automaticky aktualizuje
- [ ] Nová hodnota se automaticky vybere
- [ ] Enter v modalu uloží hodnotu
- [ ] Escape zavře modal
- [ ] Kliknutí mimo zavře dropdown

## Příklad použití

```html
{% include 'components/dropdown_widget_compact.html' with 
    field_name='manufacturer',
    field_label='Výrobce',
    category='vyrobci',
    current_value=device.manufacturer,
    placeholder='Zadejte výrobce...'
%}
```

## Migrace z původní verze

1. **Žádné změny v backendu** - API endpointy stejné
2. **Žádné změny v datech** - Kategorie a hodnoty stejné
3. **Nahradit soubor** - Stačí vyměnit HTML komponentu
4. **Otestovat** - Projít všechny formuláře s dropdowny

## Poznámky

- Modal je **sdílený** mezi všemi dropdowny na stránce (úspora kódu)
- Input je **vždy editovatelný** (volný text kdykoliv)
- Dropdown je **volitelný** (nemusíš ho vůbec použít)
- Nové hodnoty se přidávají **na konec seznamu** (před separator)

---

**Výsledek:** Elegantní, moderní a kompaktní dropdown! ✨
