# 🔍 ANALÝZA PROBLÉMŮ V NASTAVENÍ

## 📋 ZJIŠTĚNÉ PROBLÉMY

### 1. ❌ Drag-drop pro změnu pořadí NEFUNGUJE
**Stav:** Implementováno jen částečně
- ✅ Drag-drop pro přesouvání mezi kategoriemi funguje
- ❌ Drag-drop pro změnu pořadí UVNITŘ kategorie nefunguje
- ❌ Chybí aktualizace `display_order` při přesunu

**Důsledek:**
- Nemůžeš změnit pořadí polí v rámci stejné kategorie
- `display_order` se neaktualizuje → pořadí ve formulářích zůstává nezměněné

---

### 2. ❌ Nelze přejmenovat pole
**Stav:** Chybí funkce
- ❌ Nelze změnit `custom_label` (vlastní název pole)
- Pole `custom_label` existuje v databázi, ale není v UI

**Důsledek:**
- Nemůžeš si přizpůsobit názvy polí podle svých potřeb
- Musíš používat výchozí názvy

---

### 3. ❌ Nelze mazat/upravovat dropdown hodnoty
**Stav:** Částečně implementováno
- ✅ Lze přesouvat hodnoty nahoru/dolů (move-up/move-down)
- ✅ Lze mazat hodnoty (delete)
- ❌ Nelze upravovat existující hodnoty (edit)
- ❌ UI pro editaci chybí

**Důsledek:**
- Pokud se spletete v hodnotě, musíte ji smazat a vytvořit novou

---

### 4. ❌ Chybí pole pro status revize (Aktivní/Dokončeno)
**Stav:** Chybí kompletně
- `revision_end_date` se používá jako indikátor (pokud je vyplněno → dokončeno)
- Chybí explicitní status pole
- Chybí filtrování podle statusu v UI

**Důsledek:**
- Nelze snadno filtrovat aktivní vs. dokončené revize
- Logika je založena na implicitním stavu (end_date)

---

### 5. ❌ Quick-add modaly nejsou konfigurovatelné
**Stav:** Hardcoded
- Quick-add formuláře mají pevně dané pole
- Např. `quick_add_switchboard_form.html` má hardcoded:
  - switchboard_name
  - switchboard_location
  - switchboard_type
- Nelze přizpůsobit podle workflow

**Důsledek:**
- Nemůžeš si vybrat, která pole se zobrazí v quick-add
- Pro každou entitu jsou pevná pole

---

### 6. ⚠️ Kategorie neodpovídají napříč UI
**Stav:** Částečně

**V nastavení máme kategorie:**
- basic (Základní údaje)
- additional (Dodatečné údaje)
- administrative (Administrativní)
- technical (Technické)
- measurements (Měření)

**Ve formulářích (`revision_form.html`):**
- Používají dynamické renderování podle kategorií
- ✅ Funguje správně

**V inline edit kartách (`revision_edit_basic.html`):**
- Po opravě teď používají dynamické renderování
- ✅ Funguje správně

**V static kartách (`revision_static_basic.html`):**
- ❌ Hardcoded pole
- Neodpovídají konfiguraci v nastavení

**Důsledek:**
- Když skryješ pole v nastavení, zmizí z formulářů, ale zůstane ve static view
- Nekonzistence mezi tím, co vidíš při editaci vs. v přehledu

---

## 🎯 PRIORITY

### Priority 1 (Kritické):
1. ✅ **Drag-drop pro změnu pořadí v rámci kategorie**
2. ✅ **Přejmenování polí (custom_label)**
3. ✅ **Dynamic static cards** - aby respektovaly nastavení

### Priority 2 (Důležité):
4. ✅ **Editace dropdown hodnot**
5. ✅ **Status pole pro revize**

### Priority 3 (Nice to have):
6. ✅ **Konfigurovatelné quick-add modaly**

---

## 💡 NÁVRHY ŘEŠENÍ

### 1. Drag-drop pro změnu pořadí
**Implementace:**
- Přidat drag-drop UVNITŘ kategorie (ne jen mezi kategoriemi)
- Aktualizovat `display_order` podle nové pozice
- Endpoint: `/settings/field-config/{field_id}/reorder`

**Logika:**
```python
@app.post("/settings/field-config/{field_id}/reorder")
async def reorder_field(field_id: int, new_position: int, ...):
    # 1. Get field
    # 2. Get all fields in same category + entity
    # 3. Reorder based on new_position
    # 4. Update display_order for all affected fields
```

---

### 2. Přejmenování polí
**Implementace:**
- Přidat UI pro editaci `custom_label`
- Endpoint: `/settings/field-config/{field_id}/rename`
- Inline edit s ikonkou tužky u každého pole

**UI:**
```html
<div class="field-item">
  <span class="field-label">{{ field.label }}</span>
  <button onclick="openRenameModal(fieldId)">✏️</button>
</div>
```

---

### 3. Dynamic static cards
**Implementace:**
- Upravit všechny `*_static_*.html` templates
- Použít dynamické renderování místo hardcoded polí
- Podobně jako u edit kart

**Příklad:**
```html
<!-- revision_static_basic.html -->
{% for field in field_configs %}
  {% if field.category == 'basic' and field.enabled %}
    <div>
      <dt>{{ field.label }}</dt>
      <dd>{{ revision[field.name] }}</dd>
    </div>
  {% endif %}
{% endfor %}
```

---

### 4. Editace dropdown hodnot
**Implementace:**
- Přidat tlačítko ✏️ u každé hodnoty
- Modal pro editaci hodnoty
- Endpoint: `/settings/dropdown/value/{value_id}/update`

---

### 5. Status pole pro revize
**Implementace:**
**Varianta A:** Nové pole `revision_status`
```python
# models.py
revision_status = Column(String(50), default='active')  # 'active', 'completed'
```

**Varianta B:** Computed property
```python
@property
def is_active(self):
    return self.revision_end_date is None
```

**Doporučení:** Varianta B (jednodušší, žádná migrace)

---

### 6. Konfigurovatelné quick-add modaly
**Implementace:**
- Přidat tabulku `quick_add_config`
```python
class QuickAddConfig(Base):
    entity_type = Column(String)
    field_name = Column(String)
    enabled = Column(Boolean, default=True)
    display_order = Column(Integer)
```

- UI v nastavení: "Quick Add konfigurace"
- Dynamické renderování quick-add formulářů

---

## 📊 ROZSAH PRÁCE

### Soubory k úpravě:

**Backend (main.py):**
- ✅ Přidat endpoint `/settings/field-config/{field_id}/reorder`
- ✅ Přidat endpoint `/settings/field-config/{field_id}/rename`
- ✅ Upravit endpoint `/settings/dropdown/value/{value_id}/update`
- ✅ Přidat endpoint pro quick-add config (optional)

**Database (models.py):**
- ❓ Přidat `QuickAddConfig` model (optional)

**Templates:**
- ✅ `settings_redesigned.html` - přidat drag-drop pro pořadí
- ✅ `settings_redesigned.html` - přidat rename UI
- ✅ `settings_redesigned.html` - přidat edit dropdown hodnot
- ✅ Všechny `*_static_*.html` - dynamic rendering
- ✅ Všechny `quick_add_*.html` - dynamic rendering (optional)

**Odhadovaný čas:**
- Priority 1: ~3-4 hodiny
- Priority 2: ~2-3 hodiny
- Priority 3: ~2-3 hodiny
- **Celkem: 7-10 hodin práce**

---

## 🚀 POSTUPNÝ PLÁN

### Fáze 1: Kritické opravy
1. Drag-drop pro změnu pořadí
2. Přejmenování polí
3. Dynamic static cards

### Fáze 2: Důležité features
4. Editace dropdown hodnot
5. Status indikátor pro revize

### Fáze 3: Nice to have
6. Konfigurovatelné quick-add modaly

---

**Vytvořeno:** 2025-11-10  
**Status:** Analýza kompletní, čeká na implementaci
