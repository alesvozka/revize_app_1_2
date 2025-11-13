# 🐛 FÁZE 5 DROPDOWN FIX - SHRNUTÍ

## Problém
Po redesignu v Fázi 5 přestaly fungovat dropdowny v inline edit kartách.

## Příčina
Fáze 5 vytvořila **inline edit karty** pro detail stránky s **HARDCODED input fieldy**, které **IGNOROVALY** dynamickou dropdown konfiguraci z Fáze 4.

### Před opravou:
```html
<!-- templates/cards/revision_edit_basic.html -->
<input type="text" name="revision_type" value="..." />
<!-- ❌ Klasický input, žádný dropdown! -->
```

### Po opravě:
```html
<!-- templates/cards/revision_edit_basic.html -->
{% from 'components/form_field_dynamic.html' import render_dynamic_field %}
{% for field in field_configs %}
    {{ render_dynamic_field(field, revision, dropdown_sources) }}
{% endfor %}
<!-- ✅ Dynamické renderování s dropdown supportem! -->
```

## Co bylo opraveno

### 1. Backend Endpointy

**`/revision/{id}/edit-card/{card_type}`**
- ✅ Přidán `field_configs = get_entity_field_config('revision', db)`
- ✅ Přidány `dropdown_sources` (všechny kategorie a hodnoty)

**`/switchboard/{id}/edit-card/{card_type}`**
- ✅ Přidán `field_configs = get_entity_field_config('switchboard', db)`
- ✅ Přidány `dropdown_sources` (všechny kategorie a hodnoty)

### 2. Inline Edit Card Templates

Nahrazeny **hardcoded verze** za **dynamické verze**:

**Revision karty:**
- ✅ `revision_edit_basic.html` - nyní používá dynamické renderování
- ✅ `revision_edit_admin.html` - nyní používá dynamické renderování
- ✅ `revision_edit_dates.html` - nyní používá dynamické renderování

**Switchboard karty:**
- ✅ `switchboard_edit_basic.html` - nyní používá dynamické renderování
- ✅ `switchboard_edit_technical.html` - nyní používá dynamické renderování

### 3. Debug Výstupy

Přidány debug komentáře do `form_field_dynamic.html`:
```html
<!-- DEBUG FIELD: revision_type | has_dropdown=True | dropdown_category=typ_revize -->
```

## Jak to testovat

### 1. Otevři detail stránku revize
```
http://localhost:8000/revision/{revision_id}
```

### 2. Klikni na ikonu tužky u karty "Základní informace"
Měl bys vidět inline edit formulář

### 3. Zkontroluj pole s dropdownem (např. "Typ revize")
Mělo by mít:
- ✅ Input pole (můžeš psát přímo)
- ✅ Šipka vpravo (tlačítko pro dropdown)
- ✅ Po kliknutí se otevře dropdown menu
- ✅ V dropdownu jsou hodnoty z databáze
- ✅ Možnost "Přidat novou hodnotu..."

### 4. Totéž pro switchboard detail
```
http://localhost:8000/switchboard/{switchboard_id}
```

## Staré soubory (záloha)

Staré hardcoded templates byly přejmenovány:
- `revision_edit_basic_OLD.html`
- `revision_edit_admin_OLD.html`
- `revision_edit_dates_OLD.html`

Můžeš je smazat, pokud vše funguje správně.

## Poznámky

**Proč to nefungovalo v CREATE/EDIT formulářích?**
- Hlavní CREATE/EDIT formuláře (`/revision/create`, `/revision/{id}/edit`) používají `revision_form.html`, který již má dynamické renderování z Fáze 4
- Problém byl POUZE v inline edit kartách z Fáze 5

**Proč Chat udělal hardcoded karty?**
- Fáze 5 zadání vytvářelo karty pro NOVÉ funkce (inline editing)
- Chat neměl kontext o existující dropdown funkci z Fáze 4
- Proto vytvořil nejjednodušší implementaci s hardcoded fieldy

**Jak se tomu vyhnout příště?**
- Při velkých změnách (jako Fáze 5) vždy testovat VŠECHNY funkce
- Ujistit se, že nové features neruší existující funkce
- V zadání explicitně zmínit, že nové části musí respektovat existing features

---

**Vytvořeno:** 2025-11-10
**Opraveno:** Inline edit karty v Fázi 5
**Status:** ✅ FIXED
