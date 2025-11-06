# Revize App - Aplikace pro správu revizí elektrických instalací

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
│   ├── base.html                    # Základní template (sidebar, navigace)
│   ├── dashboard.html               # Dashboard s přehledem revizí
│   ├── revision_form.html           # Formulář pro CREATE/UPDATE revize
│   ├── revision_detail.html         # Detail revize (READ) + seznam switchboardů
│   ├── switchboard_form.html        # Formulář pro CREATE/UPDATE switchboard
│   └── switchboard_detail.html      # Detail switchboardu (READ)
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

### 📋 TODO - Další fáze:
- [ ] FÁZE 9: Dropdown systém (3 režimy)
- [ ] FÁZE 10: Settings (správa dropdownů)
- [ ] FÁZE 11: Duplikace funkcionalita

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

---

## 📞 Support

Pro detailní zadání projektu viz: `ZADANI_REVIZE_APP.md`

---

**Status:** ✅ FÁZE 1-5 HOTOVO - Plně funkční CRUD pro Revize + Switchboards připraven
