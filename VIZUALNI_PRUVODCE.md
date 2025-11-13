# 🎨 VIZUÁLNÍ PRŮVODCE ZMĚNAMI

## NOVÁ STRÁNKA NASTAVENÍ

### 📱 Layout

```
┌─────────────────────────────────────────────────────────────────────┐
│  ⚙️ Nastavení                                                        │
│  Konfigurace aplikace a správa formulářových polí                   │
└─────────────────────────────────────────────────────────────────────┘

┌──────────────────┬──────────────────────────────────────────────────┐
│ ENTITY           │  KONFIGURACE                                     │
│                  │                                                  │
│ ┌──────────────┐ │  ┌─────────────────┬─────────────────┐          │
│ │📋 Revize     │ │  │ 📝 Pole formul. │ 📋 Dropdowny   │          │
│ │ 29 polí      │ │  └─────────────────┴─────────────────┘          │
│ └──────────────┘ │                                                  │
│                  │  🔵 Základní pole (4)                            │
│ ┌──────────────┐ │  ┌───────────────────────────────────────────┐  │
│ │📦 Rozváděč   │ │  │ ●  Název rozváděče        [Povinné]  ●    │  │
│ │ 35 polí   <──┼─┼─>│ ●  Popis                              ●    │  │
│ └──────────────┘ │  │ ●  Umístění                           ●    │  │
│                  │  │ ●  Typ rozváděče                      ●    │  │
│ ┌──────────────┐ │  └───────────────────────────────────────────┘  │
│ │🔌 Přístroj   │ │                                                  │
│ │ 10 polí      │ │  ⚙️ Technické pole (18)                         │
│ └──────────────┘ │  ┌───────────────────────────────────────────┐  │
│                  │  │ ●  Výrobní číslo                      ○    │  │
│ ┌──────────────┐ │  │ ●  Datum výroby                       ○    │  │
│ │⚡ Obvod       │ │  │ ●  Stupeň krytí (IP)                  ●    │  │
│ │ 17 polí      │ │  │ ... (15 dalších polí)                      │  │
│ └──────────────┘ │  └───────────────────────────────────────────┘  │
│                  │                                                  │
│ ┌──────────────┐ │  📏 Měření (6) ← NOVĚ!                          │
│ │💡 Koncové    │ │  ┌───────────────────────────────────────────┐  │
│ │   zařízení   │ │  │ ●  Izolační odpor                     ○    │  │
│ │ 10 polí      │ │  │ ●  Smyčková impedance min             ○    │  │
│ └──────────────┘ │  │ ●  Smyčková impedance max             ○    │  │
│                  │  │ ●  Doba vypnutí RCD (ms)              ○    │  │
│ ───────────────  │  │ ●  Zkušební proud RCD (mA)            ○    │  │
│                  │  │ ●  Odpor uzemnění                     ○    │  │
│ 📋 Správa        │  └───────────────────────────────────────────┘  │
│    dropdownů     │                                                  │
└──────────────────┴──────────────────────────────────────────────────┘
```

### 🎯 Hlavní prvky

#### 1. ENTITY SELECTOR (levý sloupec)
```
┌─────────────────┐
│📋 Revize        │  ← Kliknutím otevřeš konfiguraci
│   29 polí       │
│                 │
│📦 Rozváděč      │  ← Aktivní (žluté pozadí)
│   35 polí       │
│                 │
│🔌 Přístroj      │
│   10 polí       │
└─────────────────┘
      Sticky!
```

#### 2. TOGGLE SWITCH
```
Vypnuto:  ○────   Zapnuto:  ────●
         šedá              žlutá (#FDB913)
```

#### 3. BADGE OZNAČENÍ
```
[Povinné]    ← Žlutý badge, pole nelze vypnout
[Dropdown]   ← Modrý badge, pole má dropdown
```

#### 4. TABS
```
┌─────────────────┬─────────────────┐
│ 📝 Pole formul. │ 📋 Dropdowny   │  ← Aktivní (žlutá)
└─────────────────┴─────────────────┘
     ▼ Obsah aktivního tabu ▼
```

## 🆕 NOVÁ POLE

### Rozváděč - Měření (6 polí)
```
📏 Měření
  ├─ measurements_switchboard_insulation_resistance
  ├─ measurements_switchboard_loop_impedance_min
  ├─ measurements_switchboard_loop_impedance_max
  ├─ measurements_switchboard_rcd_trip_time_ms
  ├─ measurements_switchboard_rcd_test_current_ma
  └─ measurements_switchboard_earth_resistance
```

### Obvod - Měření (8 polí)
```
📏 Měření
  ├─ measurements_circuit_insulation_resistance
  ├─ measurements_circuit_loop_impedance_min
  ├─ measurements_circuit_loop_impedance_max
  ├─ measurements_circuit_rcd_trip_time_ms
  ├─ measurements_circuit_rcd_test_current_ma
  ├─ measurements_circuit_earth_resistance
  ├─ measurements_circuit_continuity
  └─ measurements_circuit_order_of_phases
```

## 🔄 WORKFLOW

### Zapnutí pole:
```
1. Otevři Nastavení (/settings)
      ↓
2. Vyber entitu (např. Rozváděč)
      ↓
3. Přepni na tab "Pole formuláře"
      ↓
4. Najdi kategorii (např. Měření)
      ↓
5. Klikni na toggle switch
      ↓
6. Pole se OKAMŽITĚ zapne (AJAX)
      ↓
7. Pole se zobrazí ve formulářích
```

### Přiřazení dropdownu:
```
1. Otevři Nastavení (/settings)
      ↓
2. Vyber entitu
      ↓
3. Přepni na tab "Dropdowny"
      ↓
4. Zaškrtni checkbox u pole
      ↓
5. Vyber kategorii z dropdownu
      ↓
6. Klikni "Uložit"
      ↓
7. Pole bude mít dropdown ve formuláři
```

## 🎨 BAREVNÁ SCHÉMATA

### Před opravou:
```
Primární:  #3b82f6 (modrá)
Accent:    #10b981 (zelená)
Design:    Stíny, zaoblené rohy
```

### Po opravě:
```
Primární:  #3b82f6 (modrá)    ← Zůstalo
Accent:    #FDB913 (žlutá)    ← NOVĚ!
Design:    Flat, ostré rohy   ← NOVĚ!
```

### Použití žluté:
- Toggle switches (zapnuto)
- Aktivní tab
- Hlavní tlačítka (Uložit, Vytvořit)
- Badge "Povinné"
- Zvýraznění aktivní entity

## 📐 RESPONZIVNÍ DESIGN

### Desktop (>1024px):
```
┌──────────┬─────────────────────────┐
│  Entity  │      Konfigurace        │
│ Selector │                         │
│          │  [Tabs]                 │
│          │                         │
│  (Sticky)│  [Obsah]                │
└──────────┴─────────────────────────┘
```

### Tablet (768-1024px):
```
┌──────────┬─────────────────────────┐
│  Entity  │      Konfigurace        │
│          │                         │
│  (Sticky)│  [Tabs] [Obsah]         │
└──────────┴─────────────────────────┘
```

### Mobile (<768px):
```
┌─────────────────────────────────────┐
│         Entity Selector             │
├─────────────────────────────────────┤
│         [Tabs]                      │
├─────────────────────────────────────┤
│         [Obsah]                     │
└─────────────────────────────────────┘
```

## 🔧 TECHNICKÉ DETAILY

### AJAX Toggle:
```javascript
function toggleField(fieldId, enabled) {
    fetch('/settings/field/toggle', {
        method: 'POST',
        body: formData
    });
    // ✅ Bez reload stránky!
}
```

### Sticky Sidebar:
```css
.sticky {
    position: sticky;
    top: 1rem;
}
```

### Toggle Switch:
```html
<label class="relative inline-flex items-center cursor-pointer">
    <input type="checkbox" class="sr-only peer">
    <div class="w-11 h-6 bg-gray-200 
         peer-checked:bg-[#FDB913] 
         peer-checked:after:translate-x-full">
    </div>
</label>
```

## 📊 SROVNÁNÍ

### PŘED:
- ❌ 1026 řádků HTML
- ❌ 3 oddělené sekce (zmatečné)
- ❌ Modré tlačítka všude
- ❌ Reload stránky při změnách
- ❌ Žádné počítadlo polí
- ❌ Žádné kategorie v polích

### PO:
- ✅ 460 řádků HTML
- ✅ Logická struktura (Entity → Tabs → Pole)
- ✅ Žlutý branding (#FDB913)
- ✅ AJAX toggle (instant update)
- ✅ Živé počítadlo polí
- ✅ Seskupení podle kategorií

## 🎯 KATEGORIE POLÍ

```
🔵 basic           → Základní pole (vždy viditelné)
📎 additional      → Dodatečné pole (volitelné)
⚙️ technical       → Technické pole (pro pokročilé)
📑 administrative  → Administrativní pole (pro správu)
📏 measurements    → Měření (nově přidáno!)
```

## ✨ NOVÉ FUNKCE

1. **AJAX Toggle** - změny bez reload
2. **Sticky Sidebar** - vždy viditelný selector
3. **Badge Označení** - vizuální indikátory
4. **Živé Počítadlo** - kolik polí má každá entita
5. **Kategorizace** - logické seskupení polí
6. **Tabs** - oddělení polí a dropdownů
7. **Ikony** - emoji pro entity
8. **Flat Design** - moderní vzhled

---

**Vše je připraveno!** 🚀

Stačí spustit aplikaci a otevřít `/settings` v prohlížeči.
