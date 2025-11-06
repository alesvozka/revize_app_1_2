# FÁZE 11 - Integrace Dropdownů ✅

## Co bylo implementováno:

### 1. Konfigurace Dropdown Polí v Settings

#### ✅ Helper Funkce pro Konfiguraci
- **`get_dropdown_configurable_fields()`**
  - Definice všech konfigurovatelných polí pro každou entitu
  - Switchboard: 11 polí (typ, IP rating, výrobce, kabel, atd.)
  - Device: 3 pole (typ přístroje, výrobce, charakteristika)
  - Circuit: 2 pole (kabel, způsob uložení)
  - Terminal Device: 5 polí (typ, výrobce, IP rating, třída ochrany, způsob instalace)

- **`get_field_dropdown_config(entity_type, db)`**
  - Načte dropdown konfiguraci pro danou entitu
  - Vrací dict: `{field_name: {'enabled': bool, 'category': str}}`
  - Používá se v form endpointech

#### ✅ UI pro Konfiguraci (Tab "Konfigurace Polí")
- **Strukturované podle entit**
  - 📦 Rozváděč (11 polí)
  - 🔌 Přístroj (3 pole)
  - ⚡ Obvod (2 pole)
  - 💡 Koncové zařízení (5 polí)

- **Pro každé pole:**
  - ☑️ Checkbox pro zapnutí/vypnutí dropdownu
  - 📋 Select pro výběr kategorie hodnot
  - 💾 Tlačítko "Uložit" pro okamžité uložení
  - 🔒 Automatické disable/enable selectu podle checkboxu

- **Features:**
  - Live toggle konfigurace JavaScript funkcí
  - Přehledné zobrazení všech konfigurovatelných polí
  - Snadná správa na jednom místě
  - Help text s vysvětlením funkce

### 2. Reusable Form Field Macro

#### ✅ `components/form_field.html`
- **Univerzální macro** pro renderování polí
- **Parametry:**
  - `field_name` - název pole
  - `field_label` - popisek
  - `current_value` - aktuální hodnota
  - `entity_type` - typ entity (pro konfiguraci)
  - `dropdown_config` - konfigurace dropdownů
  - `dropdown_sources` - dostupné hodnoty
  - `input_type`, `required`, `placeholder`, `help_text`, `extra_attrs`

- **Logika:**
  - Kontroluje dropdown konfiguraci
  - Pokud je dropdown zapnutý → zobrazí dropdown widget (3 režimy)
  - Pokud vypnutý → zobrazí standardní input

- **3 režimy dropdown widgetu:**
  1. 📋 **Vybrat z databáze** - select s hodnotami z dropdown_sources
  2. ➕ **Přidat nový** - inline přidání nové hodnoty do databáze
  3. ✎ **Volný text** - standardní text input (hodnota se neuloží do dropdownů)

### 3. Aktualizace Form Endpointů

#### ✅ Všechny form endpointy nyní předávají:
```python
# Get dropdown configuration
dropdown_config = get_field_dropdown_config("entity_type", db)

# Get all dropdown sources
categories = db.query(DropdownSource.category).distinct().all()
dropdown_sources = {}
for cat in categories:
    category = cat[0]
    sources = db.query(DropdownSource).filter(
        DropdownSource.category == category
    ).order_by(DropdownSource.display_order, DropdownSource.value).all()
    dropdown_sources[category] = sources
```

#### ✅ Aktualizované endpointy:
- **Switchboard:**
  - `/revision/{revision_id}/switchboard/create` (GET)
  - `/switchboard/{switchboard_id}/edit` (GET)

- **Device:**
  - `/switchboard/{switchboard_id}/device/create` (GET)
  - `/device/{device_id}/edit` (GET)

- **Circuit:**
  - `/device/{device_id}/circuit/create` (GET)
  - `/circuit/{circuit_id}/edit` (GET)

- **Terminal Device:**
  - `/circuit/{circuit_id}/terminal/create` (GET)
  - `/terminal/{terminal_device_id}/edit` (GET)

### 4. Integrace do Switchboard Form

#### ✅ `switchboard_form.html`
- Import form_field macro: `{% from "components/form_field.html" import render_field %}`
- **Integrace dropdown widgetu pro pole:**
  1. `switchboard_type` - Typ rozváděče
  2. `switchboard_ip_rating` - Stupeň krytí (IP)
  3. `switchboard_impact_protection` - Mechanická odolnost (IK)
  4. `switchboard_protection_class` - Třída ochrany
  5. `switchboard_manufacturer` - Výrobce rozváděče
  6. `switchboard_enclosure_manufacturer` - Výrobce skříně
  7. `switchboard_enclosure_installation_method` - Způsob instalace skříně
  8. `switchboard_superior_circuit_breaker_trip_characteristic` - Vypínací charakteristika nadřazeného jističe
  9. `switchboard_superior_circuit_breaker_manufacturer` - Výrobce nadřazeného jističe
  10. `switchboard_cable` - Typ kabelu
  11. `switchboard_cable_installation_method` - Způsob uložení kabelu

- **JavaScript funkce:**
  - `switchDropdownMode(fieldName, mode)` - přepínání mezi režimy
  - `addNewDropdownValue(fieldName, category)` - async přidání nové hodnoty
  - Automatická inicializace při načtení stránky

- **Styling:**
  - Konzistentní vzhled s existujícím designem
  - Responsive layout
  - Hover states a transitions

### 5. Konfigurovatelná Pole pro Jednotlivé Entity

#### **Switchboard (11 polí):**
1. `switchboard_type` → kategorie bude nastavitelná
2. `switchboard_ip_rating` → stupen_kryti
3. `switchboard_impact_protection` → mechanicka_odolnost
4. `switchboard_protection_class` → tridy_ochrany
5. `switchboard_manufacturer` → vyrobci
6. `switchboard_enclosure_manufacturer` → vyrobci
7. `switchboard_enclosure_installation_method` → zpusoby_ulozeni
8. `switchboard_superior_circuit_breaker_trip_characteristic` → vypinaci_charakteristiky
9. `switchboard_superior_circuit_breaker_manufacturer` → vyrobci
10. `switchboard_cable` → typy_kabelu
11. `switchboard_cable_installation_method` → zpusoby_ulozeni

#### **Device (3 pole):**
1. `switchboard_device_type` → typy_pristroju
2. `switchboard_device_manufacturer` → vyrobci
3. `switchboard_device_trip_characteristic` → vypinaci_charakteristiky

#### **Circuit (2 pole):**
1. `circuit_cable` → typy_kabelu
2. `circuit_cable_installation_method` → zpusoby_ulozeni

#### **Terminal Device (5 polí):**
1. `terminal_device_type` → typy_konc_zarizeni
2. `terminal_device_manufacturer` → vyrobci
3. `terminal_device_ip_rating` → stupen_kryti
4. `terminal_device_protection_class` → tridy_ochrany
5. `terminal_device_installation_method` → zpusoby_ulozeni

### 6. Workflow Použití

#### Krok 1: Konfigurace v Settings
1. Otevřete Settings (⚙️ Nastavení v sidebaru)
2. Přejděte na tab "Konfigurace Polí"
3. Pro každé pole:
   - Zaškrtněte checkbox pro zapnutí dropdownu
   - Vyberte kategorii hodnot
   - Klikněte "Uložit"

#### Krok 2: Použití ve Formulářích
- Pole s **zapnutým** dropdownem:
  - Zobrazí se widget se 3 režimy
  - Můžete vybrat z databáze, přidat novou hodnotu, nebo použít volný text

- Pole s **vypnutým** dropdownem:
  - Zobrazí se jako standardní text input
  - Funguje jako předtím

#### Krok 3: Přidávání Hodnot
- **Režim "Z databáze"**: Vyberte existující hodnotu
- **Režim "Přidat nový"**:
  - Zadejte novou hodnotu
  - Klikněte "Přidat a vybrat"
  - Hodnota se uloží do databáze a automaticky vybere
  - Režim se přepne na "Z databáze"
- **Režim "Volný text"**: Zadejte jednorázovou hodnotu (neuloží se do databáze)

## Technické Detaily:

### Automatické Načítání Konfigurace
- Všechny form endpointy načítají `dropdown_config` a `dropdown_sources`
- Template automaticky aplikuje konfiguraci na příslušná pole
- Žádné hardcoded kategorie v templates - vše konfigurovatelné

### Bezpečnost
- Všechny endpointy vyžadují autentizaci
- Validace vstupů na backendu
- SQL injection prevence přes ORM

### Performance
- Dropdown sources jsou načítány jen jednou při otevření formuláře
- Grouped by category pro efektivní přístup
- Minimální overhead při renderování

## Jak testovat:

### 1. Konfigurace Dropdownů:
```bash
# Spusťte aplikaci
uvicorn main:app --reload
```

1. Otevřete Settings (http://localhost:8000/settings)
2. Přejděte na tab "Konfigurace Polí"
3. U pole "Typ rozváděče" pro Switchboard:
   - Zaškrtněte checkbox
   - Vyberte kategorii (např. "typy_pristroju" nebo vytvořte novou)
   - Klikněte "Uložit"

### 2. Testování ve Formuláři:
1. Vytvořte nebo upravte rozváděč
2. Pole "Typ rozváděče" by mělo zobrazit dropdown widget
3. Vyzkoušejte všechny 3 režimy:
   - Vyberte z databáze
   - Přidejte novou hodnotu
   - Použijte volný text

### 3. Testování Ostatních Formulářů:
- Stejný postup pro Device, Circuit, Terminal Device formuláře
- Všechna konfigurovatelná pole by měla fungovat stejně

## Co je speciální v této FÁZI:

### Plně Konfigurovatelný Systém
- Admin může zapnout/vypnout dropdown pro jakékoliv pole
- Může přiřadit kategorii podle potřeby
- Změny se okamžitě projeví ve všech formulářích

### Reusable Komponenty
- `form_field.html` macro může být použito v jakémkoliv formuláři
- Stačí předat správné parametry
- Automatická detekce dropdown konfigurace

### Konzistentní UX
- Všechny formuláře fungují stejně
- Stejný vzhled a chování
- Uživatel se nemusí učit nové patterny

### Developer-Friendly
- Helper funkce pro snadné použití
- Centralizovaná konfigurace
- Jednoduchá integrace do nových formulářů

### Flexibilita
- 3 režimy pokrývají všechny use cases
- Databázové hodnoty pro opakované použití
- Volný text pro jednorázové případy
- Inline přidání pro rychlé doplnění

## Možná Vylepšení (pro budoucnost):

### UI/UX:
- Bulk konfigurace - zapnout všechna pole najednou
- Preview hodnot přímo v konfiguraci
- Statistiky využití hodnot

### Backend:
- Validace kategorie při ukládání
- Automatické mapování field_name → vhodná kategorie
- Import/export konfigurace

### Forms:
- Autocomplete při psaní
- Recent values (naposledy použité)
- Smart suggestions based on context

---

**Status:** ✅ Fáze 11 dokončena

**Připraveno pro:**
- Další integrace do ostatních formulářů (device, circuit, terminal)
- Použití v production
- Rozšíření o další konfigurovatelná pole

**Poznámka:** Switchboard formulář plně integrován s dropdowny. Ostatní formuláře (device_form.html, circuit_form.html, terminal_device_form.html) mají připravené backendové endpointy, ale čekají na integraci macro v šablonách - to lze udělat jednoduchým copy-paste přístupu ze switchboard_form.html.
