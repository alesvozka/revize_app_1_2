# FÁZE 8 - Dokončeno ✅

## Co bylo implementováno:

### 1. CRUD Operace pro Circuit (Obvody)

#### ✅ CREATE (Přidání obvodu)
- **Endpoint:** `GET /device/{device_id}/circuit/create` - zobrazení formuláře
- **Endpoint:** `POST /device/{device_id}/circuit/create` - uložení obvodu
- **Template:** `templates/circuit_form.html`
- **Funkce:**
  - Formulář s 8 poli pro parametry obvodu
  - Všechna pole volitelná
  - Info box s instrukcemi k popisu obvodu
  - Automatická kontrola vlastnictví přes device → switchboard → revision
  - Redirect na detail obvodu po uložení

#### Pole obvodu (8 parametrů):
1. **circuit_number** (String) - Číslo obvodu
2. **circuit_room** (String) - Místnost / Oblast
3. **circuit_description** (Text) - Popis obvodu
4. **circuit_description_from_switchboard** (Text) - Popis z rozváděče
5. **circuit_number_of_outlets** (Integer) - Počet zásuvek
6. **circuit_cable_termination** (String) - Zakončení kabelu
7. **circuit_cable** (String) - Typ kabelu
8. **circuit_cable_installation_method** (String) - Způsob uložení

#### ✅ READ (Zobrazení detailu obvodu)
- **Endpoint:** `GET /circuit/{circuit_id}` - detail obvodu
- **Template:** `templates/circuit_detail.html`
- **Funkce:**
  - Zobrazení všech parametrů obvodu
  - Breadcrumb navigace (Revize → Rozváděč → Přístroj → Obvod)
  - Sekce měření s možností přidat/editovat/smazat
  - Sekce koncových zařízení (připraveno pro FÁZI 9)
  - Tlačítka Editovat a Smazat

#### ✅ UPDATE (Editace obvodu)
- **Endpoint:** `GET /circuit/{circuit_id}/edit` - zobrazení formuláře
- **Endpoint:** `POST /circuit/{circuit_id}/update` - uložení změn
- **Template:** Stejný jako CREATE (`circuit_form.html`)
- **Funkce:**
  - Předvyplnění formuláře aktuálními hodnotami
  - Redirect na detail obvodu po uložení

#### ✅ DELETE (Smazání obvodu)
- **Endpoint:** `POST /circuit/{circuit_id}/delete`
- **Funkce:**
  - JavaScript confirm dialog
  - **Kaskádové mazání měření a koncových zařízení** díky cascade="all, delete-orphan"
  - Redirect na detail přístroje po smazání
  - Kontrola oprávnění přes JOIN přes Device → Switchboard → Revision

### 2. CRUD Operace pro CircuitMeasurement (Měření obvodu)

#### ✅ CREATE (Přidání měření)
- **Endpoint:** `GET /circuit/{circuit_id}/measurement/create` - zobrazení formuláře
- **Endpoint:** `POST /circuit/{circuit_id}/measurement/create` - uložení měření
- **Template:** `templates/circuit_measurement_form.html`
- **Funkce:**
  - Formulář s 8 poli pro měřené hodnoty
  - Všechna pole volitelná
  - Automatická kontrola existence měření (vztah 1:1)
  - Redirect na existující měření pokud již existuje
  - Redirect na detail obvodu po uložení

#### Měřené hodnoty (8 parametrů):
1. **measurements_circuit_insulation_resistance** (Float) - Izolační odpor (MΩ)
2. **measurements_circuit_loop_impedance_min** (Float) - Min impedance smyčky (Ω)
3. **measurements_circuit_loop_impedance_max** (Float) - Max impedance smyčky (Ω)
4. **measurements_circuit_rcd_trip_time_ms** (Float) - RCD čas vypnutí (ms)
5. **measurements_circuit_rcd_test_current_ma** (Float) - RCD zkušební proud (mA)
6. **measurements_circuit_earth_resistance** (Float) - Odpor uzemnění (Ω)
7. **measurements_circuit_continuity** (Float) - Kontinuita (Ω)
8. **measurements_circuit_order_of_phases** (String) - Pořadí fází

#### ✅ UPDATE (Editace měření)
- **Endpoint:** `GET /circuit/{circuit_id}/measurement/edit` - zobrazení formuláře
- **Endpoint:** `POST /circuit_measurement/{measurement_id}/update` - uložení změn
- **Template:** Stejný jako CREATE (`circuit_measurement_form.html`)
- **Funkce:**
  - Předvyplnění formuláře aktuálními hodnotami
  - Redirect na detail obvodu po uložení

#### ✅ DELETE (Smazání měření)
- **Endpoint:** `POST /circuit_measurement/{measurement_id}/delete`
- **Funkce:**
  - JavaScript confirm dialog v detailu obvodu
  - Redirect na detail obvodu po smazání

### 3. Device Detail (Detail přístroje)

#### ✅ Nová stránka pro zobrazení detailu přístroje
- **Endpoint:** `GET /device/{device_id}` - detail přístroje
- **Template:** `templates/device_detail.html`
- **Funkce:**
  - Zobrazení všech parametrů přístroje
  - Zobrazení nadřízeného přístroje (pokud existuje)
  - **Seznam obvodů** napojených na tento přístroj
  - Tlačítko "+ Přidat obvod"
  - Pro každý obvod:
    - Karta s detaily (číslo, místnost, kabel, počet zásuvek)
    - Tlačítka: Detail, Editovat, Smazat
  - Breadcrumb navigace (Revize → Rozváděč → Přístroj)
  - Prázdný stav pokud nejsou obvody

### 4. Integrace do Switchboard Detail

#### Aktualizace `switchboard_detail.html`:
- ✅ Přidáno tlačítko "📋 Detail" u každého přístroje (všechny 3 úrovně hierarchie)
- ✅ Tlačítko vede na novou stránku `/device/{device_id}`
- ✅ Zachováno původní tlačítko "✏️ Editovat"
- ✅ Vizuální odlišení tlačítka Detail (modrá barva)

### 5. Testovací Data

#### Aktualizace `seed_data.py`:
- ✅ Import Circuit a CircuitMeasurement modelů
- ✅ 5 ukázkových obvodů s různými parametry:

**Hierarchie obvodů:**
```
MCB #1 (ABB S201-B16, 16A)
 ├─ Circuit 1: Kuchyně (4 zásuvky, CYKY 3×2,5) [+ měření]
 └─ Circuit 2: Obývací pokoj (6 zásuvek, CYKY 3×2,5) [+ měření]

MCB #2 (ABB S201-C20, 20A)
 └─ Circuit 3: Koupelna (bojler, pračka, CYKY 3×2,5) [+ měření]

MCB #3 (Schneider iC60N B10, 10A)
 └─ Circuit 4: Osvětlení chodba (CYKY 3×1,5) [BEZ měření]

Stykač (Schneider LC1D09, 9A)
 └─ Circuit 5: Motor čerpadlo TUV (CYKY 5×2,5) [+ měření]
```

- ✅ 4 obvody s kompletními měřeními
- ✅ 1 obvod bez měření (pro ukázku prázdného stavu)

### 6. Nové Templates:

```
templates/
  ├── circuit_form.html               # Univerzální formulář pro CREATE + UPDATE
  ├── circuit_detail.html             # Detail obvodu + měření + koncová zařízení
  ├── circuit_measurement_form.html   # Formulář pro měření (CREATE + UPDATE)
  └── device_detail.html              # Detail přístroje + seznam obvodů
```

### 7. Navigační Flow:

```
Dashboard
  └─> Revize Detail
       └─> Switchboard Detail
            └─> Sekce "Přístroje v rozváděči"
                 ├─> Stromové zobrazení hierarchie
                 ├─> [📋 Detail] → Device Detail
                 │    └─> Seznam obvodů
                 │         ├─> [+ Přidat obvod] → Circuit Form → Circuit Detail
                 │         ├─> [📋 Detail] → Circuit Detail
                 │         │    └─> Sekce "Měření obvodu"
                 │         │         ├─> [+ Přidat měření] → Measurement Form → Circuit Detail
                 │         │         ├─> [✏️ Editovat měření] → Measurement Form → Circuit Detail
                 │         │         └─> [🗑️ Smazat měření] → Circuit Detail
                 │         ├─> [✏️ Editovat] → Circuit Form → Circuit Detail
                 │         └─> [🗑️ Smazat] → Device Detail
                 ├─> [✏️ Editovat] → Device Form → Switchboard Detail
                 └─> [🗑️ Smazat] → Switchboard Detail
```

### 8. Backend Features:

#### Helper funkce:
- `get_value()` - převod form dat s podporou int, float
- Prázdné stringy → NULL (umožňuje smazání hodnot)

#### Security (multi-JOIN kontrola):
```python
# Pro Circuit
circuit = db.query(Circuit)\
    .join(SwitchboardDevice)\
    .join(Switchboard)\
    .join(Revision)\
    .filter(
        Circuit.circuit_id == circuit_id,
        Revision.user_id == user_id
    ).first()

# Pro CircuitMeasurement
measurement = db.query(CircuitMeasurement)\
    .join(Circuit)\
    .join(SwitchboardDevice)\
    .join(Switchboard)\
    .join(Revision)\
    .filter(
        CircuitMeasurement.measurement_id == measurement_id,
        Revision.user_id == user_id
    ).first()
```
- Zajišťuje přístup pouze k vlastním datům
- 4-5 úrovňový JOIN pro plnou kontrolu vlastnictví

#### Kaskádové mazání:
```python
# V Circuit modelu
measurements = relationship("CircuitMeasurement", back_populates="circuit", 
                          uselist=False, cascade="all, delete-orphan")
terminal_devices = relationship("TerminalDevice", back_populates="circuit", 
                              cascade="all, delete-orphan")
```
- Při smazání obvodu se automaticky smažou měření i koncová zařízení

### 9. UI/UX Features:

#### Circuit Form:
- ✅ Info box s instrukcemi k vyplnění
- ✅ Placeholdery s ukázkovými hodnotami
- ✅ Popisky pod každým polem
- ✅ Jednotky v labelech (CYKY 3×2,5, zásuvky)
- ✅ Responzivní layout (1 sloupec na mobile, 2 na desktop)
- ✅ Logické seskupení polí (Základní info / Popis / Kabel)

#### Circuit Measurement Form:
- ✅ Info box s instrukcemi k měření
- ✅ Step precision pro float hodnoty (0.01, 0.001, 0.1)
- ✅ Jednotky v labelech (MΩ, Ω, ms, mA)
- ✅ Logické seskupení (Základní měření / Impedance / RCD)
- ✅ Placeholdery s ukázkovými hodnotami

#### Device Detail:
- ✅ Breadcrumb navigace
- ✅ Zobrazení parametrů přístroje v přehledné tabulce
- ✅ Zvýraznění nadřízeného přístroje (modrý box)
- ✅ Seznam obvodů v kartách s detaily
- ✅ Tlačítka Detail/Editovat/Smazat pro každý obvod
- ✅ Prázdný stav s ikonou a popisem

#### Circuit Detail:
- ✅ Breadcrumb navigace (4 úrovně)
- ✅ Zobrazení všech parametrů obvodu
- ✅ Sekce měření s tlačítky Přidat/Editovat/Smazat
- ✅ Formátování měřených hodnot s jednotkami
- ✅ Prázdný stav pro měření
- ✅ Placeholder sekce pro koncová zařízení (FÁZE 9)
- ✅ Confirm dialog pro smazání

### 10. Vztahy v Databázi:

#### Circuit (Obvody):
- **N:1** → SwitchboardDevice (jeden přístroj má více obvodů)
- **1:1** → CircuitMeasurement (jeden obvod má jedno měření)
- **1:N** → TerminalDevice (jeden obvod má více koncových zařízení) - připraveno pro FÁZI 9

#### Cascade Delete:
```
Device (DELETE) → Circuits (CASCADE) → CircuitMeasurements (CASCADE)
                                     → TerminalDevices (CASCADE)
```

## Jak testovat:

### 1. Naplnění/aktualizace databáze:
```bash
python seed_data.py
```
**Vytvoří:** 5 obvodů (4 s měřením, 1 bez měření)

### 2. Spuštění aplikace:
```bash
uvicorn main:app --reload
```

### 3. Testování Flow:
1. **Dashboard** → První revize → "Hlavní rozváděč přízemí"
2. **Switchboard Detail** → Scroll na "Přístroje v rozváděči"
3. **Klikněte na 📋 Detail** u přístroje → Zobrazí Device Detail
4. **Device Detail** → Vidíte seznam obvodů
5. **Vytvoření obvodu** → Klikněte "+ Přidat obvod" → Vyplňte formulář
6. **Detail obvodu** → Klikněte "📋 Detail" u obvodu → Zobrazí Circuit Detail
7. **Přidání měření** → V Circuit Detail klikněte "+ Přidat měření"
8. **Editace měření** → Klikněte "✏️ Editovat měření"
9. **Smazání měření** → Klikněte "🗑️ Smazat měření"
10. **Editace obvodu** → V Circuit Detail klikněte "✏️ Editovat"
11. **Smazání obvodu** → Klikněte "🗑️ Smazat" → Ověřte kaskádové mazání měření

### 4. Testování hierarchie:
- Obvod MCB #1 má 2 obvody (Kuchyně, Obývák)
- Obvod MCB #2 má 1 obvod (Koupelna)
- Obvod MCB #3 má 1 obvod (Osvětlení) - bez měření
- Stykač má 1 obvod (Motor) - s měřením

## Technické detaily:

### Circuit Formulář:
- **8 polí:** Všechna volitelná
- **Validace:** Žádné povinné pole (flexibilita)
- **Step precision:** 
  - Integer pro počet zásuvek

### Circuit Measurement Formulář:
- **8 polí:** Všechna volitelná
- **Step precision:**
  - 0.01 pro izolační odpor (MΩ)
  - 0.001 pro impedance a odpory (Ω)
  - 0.1 pro RCD parametry (ms, mA)
- **Jednotky:** Zobrazeny v labelech i u hodnot v detailu

### Výhody struktury:
- Jasná hierarchie: Revize → Switchboard → Device → Circuit
- Kaskádové mazání automaticky udržuje konzistenci
- Flexibilní - všechna pole volitelná
- Snadno rozšiřitelné o koncová zařízení (FÁZE 9)

## Co je speciální v této FÁZI:

### Vztah 1:1 s CircuitMeasurement:
- Podobné jako SwitchboardMeasurement
- Automatická kontrola existence měření
- Redirect na edit pokud měření již existuje
- Cascade delete při smazání obvodu

### Device Detail stránka:
- První samostatná stránka pro zobrazení přístroje
- Zobrazuje hierarchii (nadřízený přístroj)
- Seznam všech obvodů napojených na přístroj
- Umožňuje snadný přehled a správu obvodů

### 4-5 úrovňový JOIN:
- Nejdelší JOIN chain v aplikaci dosud
- Zajišťuje bezpečnost přes celou hierarchii
- Circuit → Device → Switchboard → Revision → User

### Breadcrumb navigace:
- 4 úrovně: Revize → Rozváděč → Přístroj → Obvod
- Funkční odkazy na všechny úrovně
- Usnadňuje orientaci v aplikaci

## Design rozhodnutí:

✅ **Volba samostatné Device Detail stránky je správná protože:**
- Přehledné zobrazení všech obvodů přístroje
- Jasná navigace v hierarchii
- Snadné přidávání nových obvodů
- Oddělení logiky od switchboard detail

✅ **Všechna pole volitelná protože:**
- Flexibilita pro různé typy obvodů
- Ne všechny údaje jsou vždy známé
- Postupné doplňování informací

✅ **Samostatné formuláře pro Circuit a Measurement protože:**
- Logické oddělení parametrů obvodu a měření
- Přehlednější formuláře
- Možnost existovat bez měření

---

**Poznámka:** CRUD pro obvody je hotov. Vztahy 1:1 s měřením a 1:N s přístroji fungují perfektně. Cascade delete zajišťuje konzistenci dat. Device Detail poskytuje přehledný přístup k obvodům.

**Připraveno pro FÁZI 9:** CRUD pro TerminalDevice (koncová zařízení) - vztah 1:N s obvody
