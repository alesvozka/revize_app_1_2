# FÁZE 7 - Dokončeno ✅

## Co bylo implementováno:

### 1. CRUD Operace pro SwitchboardDevice (Přístroje v rozváděči)

#### ✅ CREATE (Přidání přístroje)
- **Endpoint:** `GET /switchboard/{switchboard_id}/device/create` - zobrazení formuláře
- **Endpoint:** `POST /switchboard/{switchboard_id}/device/create` - uložení přístroje
- **Template:** `templates/device_form.html`
- **Funkce:**
  - Formulář s 11 poli pro parametry přístroje
  - **Dropdown pro výběr parent device** - umožňuje vytvořit hierarchii
  - Všechna pole volitelná kromě pozice (position)
  - Info box s instrukcemi k hierarchii
  - Automatická kontrola vlastnictví přes switchboard → revision
  - Redirect na detail switchboardu po uložení

#### Pole přístroje (11 parametrů):
1. **parent_device_id** (FK) - Nadřízený přístroj (pro hierarchii)
2. **switchboard_device_position** (String) - Pozice v rozváděči **(povinné)**
3. **switchboard_device_type** (String) - Typ přístroje (RCD, MCB, Stykač)
4. **switchboard_device_manufacturer** (String) - Výrobce
5. **switchboard_device_model** (String) - Model
6. **switchboard_device_trip_characteristic** (String) - Vypínací charakteristika (B, C, D)
7. **switchboard_device_rated_current** (Float) - Jmenovitý proud (A)
8. **switchboard_device_residual_current_ma** (Float) - Vypínací proud RCD (mA)
9. **switchboard_device_poles** (Integer) - Počet pólů
10. **switchboard_device_module_width** (Float) - Šířka modulu
11. **switchboard_device_sub_devices** (Text) - Poznámka k podřazeným přístrojům

#### ✅ READ (Zobrazení stromové struktury)
- Zobrazeno přímo v detailu switchboardu (ne samostatná stránka)
- Sekce "Přístroje v rozváděči" v `switchboard_detail.html`
- **Stromové zobrazení hierarchie** (3 úrovně):
  - Root devices (žádný parent)
  - Child devices (1. úroveň) s vizuální indentací
  - Grandchild devices (2. úroveň) s větší indentací
- Vizuální označení hierarchie:
  - Ikona šipky (→) pro podřízené přístroje
  - Barevné odlišení pozadí (root = šedé, děti = bílé)
  - Odsazení vlevo (ml-8, ml-16)
- Zobrazení klíčových údajů:
  - Pozice (monofontem v rámečku)
  - Typ + jmenovitý proud
  - Výrobce + model
- Tlačítka Editovat a Smazat pro každý přístroj
- Prázdný stav pokud nejsou přístroje

#### ✅ UPDATE (Editace přístroje)
- **Endpoint:** `GET /device/{device_id}/edit` - zobrazení formuláře
- **Endpoint:** `POST /device/{device_id}/update` - uložení změn
- **Template:** Stejný jako CREATE (`device_form.html`)
- **Funkce:**
  - Předvyplnění formuláře aktuálními hodnotami
  - Dropdown parent device **vylučuje sám sebe** (nelze být svým vlastním parent)
  - Možnost změnit hierarchii (přesunout pod jiný parent)
  - Redirect na detail switchboardu po uložení

#### ✅ DELETE (Smazání přístroje)
- **Endpoint:** `POST /device/{device_id}/delete`
- **Funkce:**
  - JavaScript confirm dialog v detailu switchboardu
  - Tlačítko "Smazat" u každého přístroje
  - **Kaskádové mazání potomků** díky self-referencing relationship v modelu
  - Varování v confirm dialogu pokud má přístroj děti
  - Redirect na detail switchboardu po smazání
  - Kontrola oprávnění přes JOIN přes Switchboard a Revision

### 2. Hierarchická Struktura (Self-Referencing)

#### Vztah 1:N s self-reference:
```python
parent_device_id = Column(Integer, ForeignKey("switchboard_devices.device_id"), nullable=True)
parent_device = relationship("SwitchboardDevice", remote_side=[device_id], backref="child_devices")
```

#### Příklad hierarchie:
```
RCD (parent_device_id = NULL)
 ├─ MCB #1 (parent_device_id = RCD.id)
 ├─ MCB #2 (parent_device_id = RCD.id)
 └─ MCB #3 (parent_device_id = RCD.id)
     └─ Stykač (parent_device_id = MCB#3.id)
```

#### Výhody self-referencing:
- Neomezená úroveň vnoření (prakticky 3 úrovně stačí)
- Automatické kaskádové mazání potomků
- Jednoduché dotazování přes relationship
- Flexibilní přesuny mezi úrovněmi

### 3. Integrace se Switchboard Detail

#### Aktualizace `switchboard_detail.html`:
- ✅ Nová sekce "Přístroje v rozváděči" před sekcí měření
- ✅ Tlačítko "+ Přidat přístroj"
- ✅ Stromové zobrazení s 3 úrovněmi vnoření
- ✅ Vizuální indikace hierarchie (ikony, odsazení)
- ✅ Tlačítka Editovat/Smazat pro každý přístroj
- ✅ Prázdný stav s ikonou a popisem

### 4. Testovací Data

#### Aktualizace `seed_data.py`:
- ✅ Import SwitchboardDevice modelu
- ✅ 7 ukázkových přístrojů s hierarchií pro první switchboard:

**Hierarchie:**
```
RCD #1 (ABB F204 AC-40/0.03, 40A, 30mA)
 ├─ MCB #1 (ABB S201-B16, B, 16A)
 └─ MCB #2 (ABB S201-C20, C, 20A)

RCD #2 (Schneider iID 40A 30mA AC, 40A, 30mA)
 └─ MCB #3 (Schneider iC60N B10, B, 10A)
     └─ Stykač (Schneider LC1D09, 9A) → Motor 2.2kW
```

### 5. Nový Template:
```
templates/
  └── device_form.html    # Univerzální formulář pro CREATE + UPDATE
```

### 6. Navigační Flow:

```
Dashboard
  └─> Revize Detail
       └─> Switchboard Detail
            └─> Sekce "Přístroje v rozváděči"
                 ├─> Stromové zobrazení hierarchie
                 ├─> [+ Přidat přístroj] → Device Form → Switchboard Detail
                 ├─> [Editovat přístroj] → Device Form → Switchboard Detail
                 └─> [Smazat přístroj] → Switchboard Detail
```

### 7. Backend Features:

#### Helper funkce:
- `get_value()` - převod form dat s podporou int, float
- Prázdné stringy → NULL (umožňuje smazání hodnot)

#### Security (multi-JOIN kontrola):
```python
device = db.query(SwitchboardDevice)\
    .join(Switchboard)\
    .join(Revision)\
    .filter(
        SwitchboardDevice.device_id == device_id,
        Revision.user_id == user_id
    ).first()
```
- Zajišťuje přístup pouze k vlastním přístrojům
- Prochází přes Switchboard → Revision pro ověření vlastnictví

#### Exkluze při editaci:
- Při editaci se přístroj sám vylučuje z parent dropdown
- Nelze být svým vlastním parentem
- Předchází cyklickým závislostem

### 8. UI/UX Features:

#### Formulář:
- ✅ Info box s instrukcemi k hierarchii
- ✅ Placeholdery s ukázkovými hodnotami
- ✅ Popisky pod každým polem
- ✅ Jednotky přímo v labelu (A, mA, moduly)
- ✅ Step precision pro float hodnoty
- ✅ Responzivní layout (1 sloupec na mobile, 2 na desktop)
- ✅ **Dropdown parent device** s vizualizací hierarchie (└─)

#### Detail switchboardu:
- ✅ Sekce s border a header
- ✅ Stromová struktura s 3 úrovněmi
- ✅ Vizuální hierarchie:
  - Ikony šipek pro děti
  - Barevné odlišení (root grey, children white)
  - Progresivní odsazení (ml-8, ml-16)
- ✅ Jednotky zobrazené přímo u hodnot
- ✅ Prázdný stav s výstižnou ikonou
- ✅ Confirm dialog pro smazání (varování při dětích)

### 9. Kaskádové Mazání (Cascade Delete)

#### Automatické v SQLAlchemy:
```python
# V modelu
parent_device = relationship(
    "SwitchboardDevice", 
    remote_side=[device_id], 
    backref="child_devices"
)
```

#### Co se stane při smazání:
- **Smazání root device** → Smaže všechny děti a vnuky
- **Smazání child device** → Smaže všechny vnuky
- **Smazání leaf device** → Smaže pouze sám sebe

#### UI indikace:
- Confirm dialog informuje, pokud má přístroj potomky
- "Opravdu chcete smazat tento přístroj **a všechny podřízené přístroje**?"

## Jak testovat:

### 1. Naplnění/aktualizace databáze:
```bash
python seed_data.py
```
**Vytvoří:** 7 přístrojů s hierarchií (2 RCD, 3 MCB, 1 Stykač)

### 2. Spuštění aplikace:
```bash
uvicorn main:app --reload
```

### 3. Testování Flow:
1. **Dashboard** → První revize → "Hlavní rozváděč přízemí"
2. **Switchboard Detail** → Scroll na "Přístroje v rozváděči"
3. **Zobrazení hierarchie** → Vidíte stromovou strukturu s 3 úrovněmi
4. **Vytvoření root device** → Klikněte "+ Přidat přístroj" → Parent = žádný
5. **Vytvoření child** → Klikněte "+ Přidat přístroj" → Vyberte parent device
6. **Editace** → Klikněte "Editovat" u přístroje → změňte hodnoty nebo parent
7. **Smazání** → Klikněte "Smazat" → ověřte kaskádové mazání potomků

### 4. Testování hierarchie:
- Vytvořte RCD (root)
- Přidejte 2-3 jističe (MCB) pod RCD
- Přidejte stykač pod jeden z jističů
- Ověřte vizuální zobrazení hierarchie
- Smažte jistič → ověřte že se smazal i stykač pod ním
- Smažte RCD → ověřte že se smazaly všechny děti

## Technické detaily:

### Formulář:
- **11 polí:** 1 povinné (position), 10 volitelných
- **Parent dropdown:** Dynamicky načítá přístroje z téhož switchboardu
- **Validace:** Pouze position je required
- **Step precision:** 
  - 0.1 pro proudy a moduly (střední přesnost)

### Výhody self-referencing vztahu:
- Flexibilní hierarchie (prakticky neomezená hloubka)
- Jednoduchá implementace (jediná tabulka)
- Automatické kaskádové mazání
- Snadné dotazování potomků přes backref

### Nevýhody (trade-offs):
- Nutnost rekurzivního procházení pro hluboké hierarchie (ale 3 úrovně stačí)
- Nelze snadno omezit maximální hloubku hierarchie
- Pro složitější struktury by bylo lepší použít Materialized Path nebo Nested Sets

## Možná vylepšení (pro budoucí fáze):

### Zobrazení:
- Rekurzivní Jinja2 macro pro neomezené úrovně vnoření
- Drag & drop pro změnu hierarchie
- Collapse/expand pro větve stromu
- Barevné kódování podle typu (RCD zelené, MCB modré)

### Funkce:
- Export struktury do PDF/Excel
- Duplikace přístroje včetně všech potomků
- Bulk operace (přesun více přístrojů najednou)
- Validace hierarchie (např. MCB nemůže být pod Stykačem)

### Integrace:
- Přiřazení obvodů (Circuit) k přístrojům
- Zobrazení počtu obvodů u každého přístroje
- Rychlý přechod z přístroje na jeho obvody

## Co je speciální v této FÁZI:

### Self-Referencing Relationship:
- První implementace self-referencing FK (oproti simple FK u předchozích vztahů)
- Backref automaticky vytváří `child_devices` property
- Kaskádové mazání funguje automaticky díky SQLAlchemy

### Stromová Struktura v UI:
- První implementace hierarchického zobrazení
- Vizuální indikace hloubky (odsazení, ikony)
- Podpora 3 úrovní vnoření v templatu
- Conditional rendering podle existence potomků

### Design rozhodnutí:
✅ **Volba self-referencing vztahu je správná protože:**
- Flexibilní struktura (RCD → MCB → Sub-device)
- Jednoduchá implementace (jediná tabulka)
- Automatické kaskádové mazání
- Pro typické případy (2-3 úrovně) je ideální

---

**Poznámka:** CRUD pro přístroje v rozváděči je hotov. Self-referencing hierarchie funguje perfektně s automatickým kaskádovým mazáním a stromovým zobrazením.

**Připraveno pro FÁZI 8:** CRUD pro Circuit (obvody) - vztah 1:N s přístroji + CircuitMeasurement (1:1)
