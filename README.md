# Revize App - Aplikace pro správu revizí elektrických instalací

## 📋 O aplikaci
Webová aplikace pro správu a zpracování revizí elektrických instalací v terénu. Postaveno na FastAPI + PostgreSQL + Tailwind CSS.

## ✅ Implementované fáze

### FÁZE 1-3: Database + Base Template + Dashboard ✅
- PostgreSQL databáze s 10 tabulkami
- Base template s responzivní navigací (mobile + desktop)
- Dashboard se seznamem revizí a statistikami

### FÁZE 4: CRUD Revize ✅
- Kompletní CRUD operace pro revize
- Formulář se všemi 32 parametry revize
- Detail revize se seznamem rozváděčů

### FÁZE 5: CRUD Rozváděče (Switchboards) ✅
- Kompletní CRUD operace pro rozváděče
- Vztah 1:N (Revision → Switchboards)
- Detail s technickými parametry (22 polí)

### FÁZE 6: CRUD Měření Rozváděčů ✅
- Kompletní CRUD operace pro měření
- Vztah 1:1 (Switchboard → Measurement)
- 6 měřených hodnot (izolační odpor, impedance smyčky, RCD parametry, uzemnění)

### FÁZE 7: CRUD Přístroje v Rozváděči ✅
- Kompletní CRUD operace pro přístroje
- **Self-referencing hierarchie** (parent_device_id)
- **Stromové zobrazení** s 3 úrovněmi vnoření
- Struktura: RCD → MCB → Sub-device (stykač, motorový spouštěč)
- **Kaskádové mazání** potomků
- 11 parametrů přístroje

### FÁZE 8: CRUD Obvody ✅
- Kompletní CRUD operace pro obvody
- **Device Detail stránka** se seznamem obvodů
- Vztah N:1 s přístrojem (device_id)
- **Circuit Measurement** (vztah 1:1) s 8 měřeními
- **Kaskádové mazání** měření a koncových zařízení
- 8 parametrů obvodu + 8 měřených hodnot
- Připraveno pro koncová zařízení (FÁZE 9)

### FÁZE 9: CRUD Koncová zařízení 🆕 ✅
- Kompletní CRUD operace pro koncová zařízení
- **Terminal Device Detail stránka**
- Vztah N:1 s obvodem (circuit_id)
- **5-úrovňový JOIN** (nejdelší v aplikaci)
- **Kaskádové mazání** při smazání obvodu
- 10 parametrů (typ, výrobce, model, výkon, IP, atd.)
- Integrace do Circuit Detail

### 📊 Aktuální pokrytí:
- ✅ Users (základní struktura, fake auth)
- ✅ Revisions (kompletní CRUD)
- ✅ Switchboards (kompletní CRUD)
- ✅ SwitchboardMeasurement (kompletní CRUD)
- ✅ SwitchboardDevice (kompletní CRUD + hierarchie)
- ✅ Circuits (kompletní CRUD)
- ✅ CircuitMeasurement (kompletní CRUD)
- ✅ TerminalDevices (kompletní CRUD) **← NOVĚ!**
- ⏳ Dropdowns (připraveno v modelu)

## 🚀 Quick Start

### Lokální vývoj

1. **Nainstaluj dependencies:**
```bash
pip install -r requirements.txt
```

2. **Nastav environment variables:**
```bash
cp .env.example .env
# Uprav .env s tvými PostgreSQL credentials
```

3. **Spusť aplikaci:**
```bash
uvicorn main:app --reload
```

4. **Otevři prohlížeč:**
```
http://localhost:8000
```

5. **Naplň databázi testovacími daty (doporučeno):**
```bash
python seed_data.py
```
Vytvoří:
- Výchozího uživatele (admin)
- 5 ukázkových revizí
- 3 rozváděče pro první revizi
- 2 měření pro první dva rozváděče
- 7 přístrojů s hierarchií (2 RCD → 3 MCB → 1 Stykač)
- 5 obvodů s měřeními (4 obvody s měřením, 1 bez)
- **7 koncových zařízení** (světla, spotřebiče, motor) 🆕

---

## 🚂 Deployment na Railway

### Krok 1: Příprava projektu
1. Pushni projekt na GitHub
2. Přihlaš se na [Railway.app](https://railway.app)

### Krok 2: Vytvoř PostgreSQL databázi
1. Vytvoř nový projekt v Railway
2. Klikni na "+ New" → "Database" → "Add PostgreSQL"
3. Railway automaticky nastaví `DATABASE_URL`

### Krok 3: Deploy aplikace
1. Klikni na "+ New" → "GitHub Repo"
2. Vyber svůj repository
3. Railway automaticky detekuje `railway.toml`
4. Nastav environment variable:
   - `SECRET_KEY` (vygeneruj: `python -c "import secrets; print(secrets.token_urlsafe(32))"`)

### Krok 4: Connect Database
1. V nastavení aplikace přidej PostgreSQL service jako variable reference
2. Railway automaticky propojí `DATABASE_URL`

---

## 📁 Struktura projektu

```
revize-app/
├── main.py                           # FastAPI aplikace + CRUD endpointy
├── models.py                         # SQLAlchemy modely (10 tabulek)
├── database.py                       # Database setup
├── requirements.txt                  # Python dependencies
├── railway.toml                      # Railway konfigurace
├── .env.example                      # Template pro environment variables
├── templates/
│   ├── base.html                     # Základní template (sidebar, navigace)
│   ├── dashboard.html                # Dashboard s přehledem revizí
│   ├── revision_form.html            # Formulář pro CREATE/UPDATE revize
│   ├── revision_detail.html          # Detail revize (READ) + seznam switchboardů
│   ├── switchboard_form.html         # Formulář pro CREATE/UPDATE switchboard
│   ├── switchboard_detail.html       # Detail switchboardu (READ) + měření + přístroje
│   ├── measurement_form.html         # Formulář pro CREATE/UPDATE měření switchboardu
│   ├── device_form.html              # Formulář pro CREATE/UPDATE přístroje
│   ├── device_detail.html            # Detail přístroje (READ) + seznam obvodů
│   ├── circuit_form.html             # Formulář pro CREATE/UPDATE obvodu
│   ├── circuit_detail.html           # Detail obvodu (READ) + měření + koncová zařízení
│   ├── circuit_measurement_form.html # Formulář pro CREATE/UPDATE měření obvodu
│   ├── terminal_device_form.html     # Formulář pro CREATE/UPDATE koncového zařízení 🆕
│   └── terminal_device_detail.html   # Detail koncového zařízení (READ) 🆕
├── static/                           # Statické soubory (prázdné)
├── seed_data.py                      # Skript pro testovací data
└── README.md                         # Tento soubor
```

---

## 🗄️ Databázové tabulky

1. **users** - Uživatelé (připraveno pro budoucí autentizaci)
2. **revisions** - Revize (29 atributů)
3. **switchboards** - Rozváděče (28 atributů)
4. **switchboard_measurements** - Měření rozváděčů (1:1)
5. **switchboard_devices** - Přístroje v rozváděči (s hierarchií)
6. **circuits** - Obvody
7. **circuit_measurements** - Měření obvodů (1:1)
8. **terminal_devices** - Koncová zařízení
9. **dropdown_sources** - Centrální tabulka pro dropdown hodnoty
10. **dropdown_config** - Konfigurace dropdownů

---

## 🔧 Aktuální stav projektu

### ✅ HOTOVO - FÁZE 1:
- Database setup
- Všechny SQLAlchemy modely
- FastAPI kostra
- Session management (default user_id=1)

### ✅ HOTOVO - FÁZE 2:
- Base template (base.html)
- Tailwind CSS + HTMX setup
- Mobile bottom navigation (Dashboard | Nová revize | Aktuální)
- Desktop sidebar (collapsible, ikony)
- Dashboard template (testovací stránka)

### ✅ HOTOVO - FÁZE 3:
- Dashboard zobrazuje skutečná data z databáze
- Statistiky: Celkem revizí, Aktivní revize, Dokončené revize
- Seznam revizí s detaily (název, kód, klient, adresa, datum)
- Status badge (Aktivní/Dokončeno) podle revision_end_date

### ✅ HOTOVO - FÁZE 4:
- **CRUD pro Revize** - kompletní implementace:
  - ✅ CREATE: Formulář pro vytvoření nové revize (všech 29 atributů)
  - ✅ READ: Zobrazení detailu revize s přehledným zobrazením všech sekcí
  - ✅ UPDATE: Editace revize (stejný formulář jako CREATE)
  - ✅ DELETE: Smazání revize s potvrzením
- Klikatelné karty revizí v dashboardu vedoucí na detail
- Responzivní formuláře s logickým seskupením polí
- Validace (povinné pole: revision_name)

### ✅ HOTOVO - FÁZE 5:
- **CRUD pro Switchboards (Rozváděče)** - kompletní implementace:
  - ✅ CREATE: Formulář pro vytvoření nového rozváděče (všech 28 atributů)
  - ✅ READ: Zobrazení detailu rozváděče s přehledným zobrazením všech sekcí
  - ✅ UPDATE: Editace rozváděče (stejný formulář jako CREATE)
  - ✅ DELETE: Smazání rozváděče s potvrzením
- Seznam rozváděčů v detailu revize
- Vazba Revision 1:N Switchboard
- Klikatelné karty rozváděčů vedoucí na detail
- Navigace: Dashboard → Revize → Switchboard
- Testovací data (3 switchboardy v první revizi)

### ✅ HOTOVO - FÁZE 6:
- **CRUD pro SwitchboardMeasurement (Měření rozváděčů)** - kompletní implementace:
  - ✅ CREATE: Formulář pro přidání měření (6 měřených hodnot)
  - ✅ UPDATE: Editace měření (stejný formulář jako CREATE)
  - ✅ DELETE: Smazání měření s potvrzením
  - ℹ️ READ: Zobrazeno přímo v detailu switchboardu (vztah 1:1)
- Vazba Switchboard 1:1 SwitchboardMeasurement
- Automatická kontrola existence měření (1:1 vztah)
- Sekce měření v detailu switchboardu
- Testovací data (2 měření pro první dva switchboardy)

### FÁZE 7: CRUD Přístroje v Rozváděči ✅
- **CRUD pro SwitchboardDevice (Přístroje v rozváděči)** - kompletní implementace:
  - ✅ CREATE: Formulář pro vytvoření nového přístroje (11 atributů)
  - ✅ READ: Stromové zobrazení v detailu switchboardu (3 úrovně hierarchie)
  - ✅ UPDATE: Editace přístroje (stejný formulář jako CREATE)
  - ✅ DELETE: Smazání přístroje s potvrzením (kaskádové mazání potomků)
- Self-referencing hierarchie (parent_device_id)
- Vazba SwitchboardDevice N:1 Switchboard
- Vazba SwitchboardDevice 1:N SwitchboardDevice (parent → children)
- Stromové zobrazení s 3 úrovněmi (RCD → MCB → Sub-device)
- Kaskádové mazání potomků
- Testovací data (7 přístrojů s hierarchií)

### FÁZE 8: CRUD Obvody ✅ 🆕
- **CRUD pro Circuit (Obvody)** - kompletní implementace:
  - ✅ CREATE: Formulář pro vytvoření nového obvodu (8 atributů)
  - ✅ READ: Detail obvodu + seznam měření a koncových zařízení
  - ✅ UPDATE: Editace obvodu (stejný formulář jako CREATE)
  - ✅ DELETE: Smazání obvodu s potvrzením (kaskádové mazání měření)
- **CRUD pro CircuitMeasurement (Měření obvodů)** - kompletní implementace:
  - ✅ CREATE: Formulář pro přidání měření (8 měřených hodnot)
  - ✅ UPDATE: Editace měření (stejný formulář jako CREATE)
  - ✅ DELETE: Smazání měření s potvrzením
  - ℹ️ READ: Zobrazeno přímo v detailu obvodu (vztah 1:1)
- **Device Detail stránka** se seznamem obvodů
- Vazba Circuit N:1 SwitchboardDevice
- Vazba Circuit 1:1 CircuitMeasurement
- Vazba Circuit 1:N TerminalDevice (připraveno)
- Automatická kontrola existence měření (1:1 vztah)
- Kaskádové mazání měření a koncových zařízení
- Testovací data (5 obvodů, 4 s měřením)

### FÁZE 9: CRUD Koncová zařízení ✅ 🆕
- **CRUD pro TerminalDevice (Koncová zařízení)** - kompletní implementace:
  - ✅ CREATE: Formulář pro vytvoření nového koncového zařízení (10 atributů)
  - ✅ READ: Detail koncového zařízení + zobrazení v seznamu obvodu
  - ✅ UPDATE: Editace zařízení (stejný formulář jako CREATE)
  - ✅ DELETE: Smazání zařízení s potvrzením
- **Terminal Device Detail stránka**
- Vazba TerminalDevice N:1 Circuit
- **5-úrovňový JOIN** (Terminal → Circuit → Device → Switchboard → Revision)
- Kaskádové mazání při smazání obvodu
- Integrace do Circuit Detail s plně funkčním CRUD rozhraním
- Testovací data (7 koncových zařízení - světla, spotřebiče, motor)

### 📋 TODO - Další fáze:
- [ ] FÁZE 10: Dropdown systém (3 režimy)
- [ ] FÁZE 11: Settings (správa dropdownů)
- [ ] FÁZE 12: Duplikace funkcionalita

---

## 🎨 UI Features

### Responzivní navigace:
- **Mobile (< 768px):** Fixed bottom navigation bar (3 položky)
- **Desktop (≥ 768px):** Collapsible sidebar s ikonami

### Dostupné stránky:
- `/` - Dashboard (základní layout s kartami)
- `/health` - Health check endpoint

### Revision CRUD endpointy:
- `GET /revision/create` - Formulář pro novou revizi
- `POST /revision/create` - Uložení nové revize
- `GET /revision/{id}` - Detail revize
- `GET /revision/{id}/edit` - Formulář pro editaci revize
- `POST /revision/{id}/update` - Uložení změn revize
- `POST /revision/{id}/delete` - Smazání revize

### Switchboard CRUD endpointy:
- `GET /revision/{revision_id}/switchboard/create` - Formulář pro nový rozváděč
- `POST /revision/{revision_id}/switchboard/create` - Uložení nového rozváděče
- `GET /switchboard/{id}` - Detail rozváděče
- `GET /switchboard/{id}/edit` - Formulář pro editaci rozváděče
- `POST /switchboard/{id}/update` - Uložení změn rozváděče
- `POST /switchboard/{id}/delete` - Smazání rozváděče

### SwitchboardMeasurement CRUD endpointy:
- `GET /switchboard/{switchboard_id}/measurement/create` - Formulář pro nové měření
- `POST /switchboard/{switchboard_id}/measurement/create` - Uložení nového měření
- `GET /switchboard/{switchboard_id}/measurement/edit` - Formulář pro editaci měření
- `POST /measurement/{id}/update` - Uložení změn měření
- `POST /measurement/{id}/delete` - Smazání měření

---

## 📞 Support

Pro detailní zadání projektu viz: `ZADANI_REVIZE_APP.md`

---

**Status:** ✅ FÁZE 1-9 HOTOVO - Plně funkční CRUD pro celou hierarchii revizí (Revize → Rozváděče → Přístroje → Obvody → Koncová zařízení + všechna měření)
