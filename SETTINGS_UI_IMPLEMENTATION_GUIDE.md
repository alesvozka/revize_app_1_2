# 🔧 IMPLEMENTAČNÍ PRŮVODCE - VYLEPŠENÍ NASTAVENÍ

## ✅ CO UŽ JE HOTOVÉ (Backend)

### Nové endpointy v `main.py`:

1. **`/settings/field-config/reorder`** (POST)
   - Přeřadí pole v rámci kategorie
   - Přijímá JSON: `{entity_type, category, field_order: [ids]}`

2. **`/settings/field-config/{field_id}/rename`** (POST)
   - Přejmenuje pole (nastaví custom_label)
   - Přijímá: `custom_label`

3. **`/settings/field-config/{field_id}/move-up`** (POST)
   - Posune pole o 1 pozici nahoru

4. **`/settings/field-config/{field_id}/move-down`** (POST)
   - Posune pole o 1 pozici dolů

5. **`/settings/dropdown/value/{value_id}/edit`** (POST)
   - Edituje existující dropdown hodnotu
   - Přijímá: `value`

---

## 🎨 CO ZBÝVÁ (Frontend)

### Změny v `templates/settings_redesigned.html`:

---

### 1. Přidat tlačítka ↑/↓ k polím

**Kde:** V sekci "Viditelnost polí" (field visibility)

**Najdi řádek ~380** (v bloku s `<div class="flex items-center gap-3 p-3...">`):

**PŘED:**
```html
<div class="flex items-center gap-3 p-3 rounded-lg border...">
    <!-- Drag handle icon -->
    <svg class="w-4 h-4...">...</svg>
    
    <!-- Toggle -->
    <input type="checkbox"...>
    
    <!-- Field Info -->
    <div class="flex-1">
        ...
    </div>
</div>
```

**PO:**
```html
<div class="flex items-center gap-3 p-3 rounded-lg border...">
    <!-- Drag handle icon -->
    <svg class="w-4 h-4...">...</svg>
    
    <!-- Toggle -->
    <input type="checkbox"...>
    
    <!-- Field Info -->
    <div class="flex-1">
        ...
    </div>
    
    <!-- 🔧 NOVÉ: Action buttons -->
    <div class="flex items-center gap-1">
        <!-- Move up -->
        <button type="button"
                onclick="moveFieldUp({{ field.id }})"
                class="p-1 text-gray-400 hover:text-primary transition"
                title="Posunout nahoru">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 15l7-7 7 7"></path>
            </svg>
        </button>
        
        <!-- Move down -->
        <button type="button"
                onclick="moveFieldDown({{ field.id }})"
                class="p-1 text-gray-400 hover:text-primary transition"
                title="Posunout dolů">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7"></path>
            </svg>
        </button>
        
        <!-- Rename -->
        <button type="button"
                onclick="openRenameFieldModal({{ field.id }}, '{{ field.label }}')"
                class="p-1 text-gray-400 hover:text-primary transition"
                title="Přejmenovat">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
            </svg>
        </button>
    </div>
</div>
```

---

### 2. Přidat tlačítko ✏️ k dropdown hodnotám

**Kde:** V sekci "Správa dropdown hodnot"

**Najdi řádek ~60-70** (v bloku s dropdown hodnotami):

**PŘED:**
```html
<div class="flex items-center justify-between p-3 rounded border hover:bg-gray-50">
    <span>{{ source.value }}</span>
    <div class="flex items-center gap-1">
        <!-- Move up -->
        <form method="POST" action="..." class="inline">
            <button>↑</button>
        </form>
        <!-- Move down -->
        ...
        <!-- Delete -->
        ...
    </div>
</div>
```

**PO:**
```html
<div class="flex items-center justify-between p-3 rounded border hover:bg-gray-50">
    <span id="value-{{ source.id }}">{{ source.value }}</span>
    <div class="flex items-center gap-1">
        <!-- 🔧 NOVÉ: Edit button -->
        <button type="button"
                onclick="openEditValueModal({{ source.id }}, '{{ source.value }}')"
                class="p-1 text-gray-400 hover:text-primary transition"
                title="Editovat">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z"></path>
            </svg>
        </button>
        
        <!-- Move up -->
        <form method="POST" action="..." class="inline">
            <button>↑</button>
        </form>
        <!-- Move down -->
        ...
        <!-- Delete -->
        ...
    </div>
</div>
```

---

### 3. Přidat modaly pro editaci

**Na konec <body>** (před `</body>`):

```html
<!-- 🔧 NOVÝ: Rename Field Modal -->
<div id="rename-field-modal" class="modal-overlay fixed inset-0 bg-black bg-opacity-50 z-50 hidden flex items-center justify-center">
    <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4" onclick="event.stopPropagation()">
        <div class="p-6">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">Přejmenovat pole</h3>
            
            <form id="rename-field-form" onsubmit="submitRenameField(event)">
                <input type="hidden" id="rename-field-id" name="field_id">
                
                <div class="mb-4">
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Vlastní název
                    </label>
                    <input type="text" 
                           id="rename-field-label" 
                           name="custom_label"
                           placeholder="Nechte prázdné pro výchozí název"
                           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent">
                    <p class="mt-1 text-xs text-gray-500">Tip: Prázdné pole obnoví výchozí název</p>
                </div>
                
                <div class="flex items-center space-x-2">
                    <button type="submit"
                            class="flex-1 bg-primary text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition font-medium">
                        💾 Uložit
                    </button>
                    <button type="button"
                            onclick="closeRenameFieldModal()"
                            class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition">
                        Zrušit
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>

<!-- 🔧 NOVÝ: Edit Dropdown Value Modal -->
<div id="edit-value-modal" class="modal-overlay fixed inset-0 bg-black bg-opacity-50 z-50 hidden flex items-center justify-center">
    <div class="bg-white rounded-lg shadow-xl max-w-md w-full mx-4" onclick="event.stopPropagation()">
        <div class="p-6">
            <h3 class="text-lg font-semibold text-gray-900 mb-4">Editovat hodnotu</h3>
            
            <form id="edit-value-form" onsubmit="submitEditValue(event)">
                <input type="hidden" id="edit-value-id" name="value_id">
                
                <div class="mb-4">
                    <label class="block text-sm font-medium text-gray-700 mb-2">
                        Hodnota
                    </label>
                    <input type="text" 
                           id="edit-value-text" 
                           name="value"
                           required
                           class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent">
                </div>
                
                <div class="flex items-center space-x-2">
                    <button type="submit"
                            class="flex-1 bg-primary text-white px-4 py-2 rounded-lg hover:bg-blue-600 transition font-medium">
                        💾 Uložit
                    </button>
                    <button type="button"
                            onclick="closeEditValueModal()"
                            class="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50 transition">
                        Zrušit
                    </button>
                </div>
            </form>
        </div>
    </div>
</div>
```

---

### 4. Přidat JavaScript funkce

**Na konec `<script>` sekce** (před `</script>`):

```javascript
// ==========================================
// 🔧 NOVÉ FUNKCE
// ==========================================

// Move field up
async function moveFieldUp(fieldId) {
    try {
        const response = await fetch(`/settings/field-config/${fieldId}/move-up`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            location.reload(); // Reload to show new order
        } else {
            alert(data.error || 'Chyba při přesunu pole');
        }
    } catch (error) {
        console.error('Error moving field up:', error);
        alert('Chyba při přesunu pole');
    }
}

// Move field down
async function moveFieldDown(fieldId) {
    try {
        const response = await fetch(`/settings/field-config/${fieldId}/move-down`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (data.success) {
            location.reload(); // Reload to show new order
        } else {
            alert(data.error || 'Chyba při přesunu pole');
        }
    } catch (error) {
        console.error('Error moving field down:', error);
        alert('Chyba při přesunu pole');
    }
}

// Open rename field modal
function openRenameFieldModal(fieldId, currentLabel) {
    document.getElementById('rename-field-id').value = fieldId;
    document.getElementById('rename-field-label').value = '';
    document.getElementById('rename-field-label').placeholder = `Výchozí: ${currentLabel}`;
    document.getElementById('rename-field-modal').classList.remove('hidden');
}

// Close rename field modal
function closeRenameFieldModal() {
    document.getElementById('rename-field-modal').classList.add('hidden');
}

// Submit rename field
async function submitRenameField(event) {
    event.preventDefault();
    
    const fieldId = document.getElementById('rename-field-id').value;
    const customLabel = document.getElementById('rename-field-label').value.trim();
    
    try {
        const formData = new FormData();
        formData.append('custom_label', customLabel);
        
        const response = await fetch(`/settings/field-config/${fieldId}/rename`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            closeRenameFieldModal();
            location.reload(); // Reload to show new label
        } else {
            alert(data.error || 'Chyba při přejmenování');
        }
    } catch (error) {
        console.error('Error renaming field:', error);
        alert('Chyba při přejmenování pole');
    }
}

// Open edit value modal
function openEditValueModal(valueId, currentValue) {
    document.getElementById('edit-value-id').value = valueId;
    document.getElementById('edit-value-text').value = currentValue;
    document.getElementById('edit-value-modal').classList.remove('hidden');
}

// Close edit value modal
function closeEditValueModal() {
    document.getElementById('edit-value-modal').classList.add('hidden');
}

// Submit edit value
async function submitEditValue(event) {
    event.preventDefault();
    
    const valueId = document.getElementById('edit-value-id').value;
    const newValue = document.getElementById('edit-value-text').value.trim();
    
    if (!newValue) {
        alert('Hodnota nemůže být prázdná');
        return;
    }
    
    try {
        const formData = new FormData();
        formData.append('value', newValue);
        
        const response = await fetch(`/settings/dropdown/value/${valueId}/edit`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (data.success) {
            // Update value in UI without reload
            document.getElementById(`value-${valueId}`).textContent = data.value;
            closeEditValueModal();
        } else {
            alert(data.error || 'Chyba při editaci hodnoty');
        }
    } catch (error) {
        console.error('Error editing value:', error);
        alert('Chyba při editaci hodnoty');
    }
}

// Close modals on click outside
document.getElementById('rename-field-modal')?.addEventListener('click', closeRenameFieldModal);
document.getElementById('edit-value-modal')?.addEventListener('click', closeEditValueModal);
```

---

## 🚀 JAK TO IMPLEMENTOVAT

### Varianta A: Manuální úprava
1. Otevři `templates/settings_redesigned.html`
2. Postupně přidej změny podle sekc

í výše
3. Testuj po každé změně

### Varianta B: Automatická náhrada
Použij tento soubor jako návod a vytvoř nový `settings_redesigned_v2.html`

---

## ✅ CHECKLIST

Po implementaci zkontroluj:

- [ ] Tlačítka ↑/↓ u polí fungují
- [ ] Tlačítko ✏️ u polí otevře modal pro přejmenování
- [ ] Přejmenování pole funguje
- [ ] Tlačítko ✏️ u dropdown hodnot otevře modal
- [ ] Editace dropdown hodnoty funguje
- [ ] Modaly se zavírají správně
- [ ] Po změně pořadí/názvu se UI aktualizuje

---

**Status:** Backend hotový ✅, Frontend čeká na implementaci 🔨
**Odhadovaný čas implementace:** 30-45 minut
