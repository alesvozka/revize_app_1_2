# PATCH PRO MAIN.PY - UNIFIED CARDS SYSTEM
# =========================================
# Tento soubor obsahuje změny pro main.py pro podporu unified card systému

# ============================================================================
# 1. UPRAVIT REVISION_DETAIL ENDPOINT
# ============================================================================

# NAJDI ŘÁDEK ~635 s funkcí:
# async def revision_detail(revision_id: int, request: Request, db: Session = Depends(get_db)):

# NAHRAĎ CELOU FUNKCI TÍMTO:

@app.get("/revision/{revision_id}", response_class=HTMLResponse)
async def revision_detail(revision_id: int, request: Request, db: Session = Depends(get_db)):
    """Detail revize - UNIFIED VERSION s dynamickými kartami"""
    user_id = get_current_user(request)
    revision = db.query(Revision).filter(
        Revision.revision_id == revision_id,
        Revision.user_id == user_id
    ).first()
    
    if not revision:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    # PHASE 6: Load field configs pro dynamické karty
    field_configs = get_entity_field_config('revision', db)
    
    # Load dropdown sources
    categories = db.query(DropdownSource.category).distinct().all()
    dropdown_sources = {}
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    return templates.TemplateResponse("revision_detail_unified.html", {
        "request": request,
        "user_id": user_id,
        "revision": revision,
        "field_configs": field_configs,
        "dropdown_sources": dropdown_sources,
        "sidebar_revisions": get_sidebar_revisions(db, user_id),
        "current_revision_for_sidebar": revision
    })


# ============================================================================
# 2. UPRAVIT GET_REVISION_CARD ENDPOINT (static karty)
# ============================================================================

# NAJDI ŘÁDEK ~656 s funkcí:
# async def get_revision_card(revision_id: int, card_type: str, ...

# NAHRAĎ CELOU FUNKCI TÍMTO:

@app.get("/revision/{revision_id}/card/{card_type}", response_class=HTMLResponse)
async def get_revision_card(revision_id: int, card_type: str, request: Request, db: Session = Depends(get_db)):
    """Return static view of a specific card - UNIFIED VERSION"""
    user_id = get_current_user(request)
    revision = db.query(Revision).filter(
        Revision.revision_id == revision_id,
        Revision.user_id == user_id
    ).first()
    
    if not revision:
        return HTMLResponse(content="<div class='p-4 text-red-500'>Revize nenalezena</div>", status_code=404)
    
    # PHASE 6: Load field configs pro dynamické static karty
    field_configs = get_entity_field_config('revision', db)
    
    # Import makra a vygeneruj kartu dynamicky
    from jinja2 import Template
    
    # Načti template s makrem
    template_str = """
    {% from 'components/dynamic_cards.html' import render_static_card %}
    {{ render_static_card(card_type, field_configs, revision, 'card-' ~ card_type) }}
    """
    
    template = templates.env.from_string(template_str)
    return HTMLResponse(content=template.render(
        card_type=card_type,
        field_configs=field_configs,
        revision=revision
    ))


# ============================================================================
# 3. STEJNÁ ÚPRAVA PRO SWITCHBOARD DETAIL
# ============================================================================

# Stejným způsobem uprav:
# - switchboard_detail endpoint (~řádek 1500)
# - get_switchboard_card endpoint (~řádek 1526)

# Použij stejnou logiku:
# 1. Load field_configs = get_entity_field_config('switchboard', db)
# 2. Load dropdown_sources
# 3. Pass do template
# 4. Template: switchboard_detail_unified.html (vytvoř stejně jako revision)


# ============================================================================
# POZNÁMKY
# ============================================================================

# Po aplikování těchto změn:
# 1. Unified systém bude fungovat pro revision detail view
# 2. Karty se budou generovat dynamicky podle field_config
# 3. Respektuje enabled/disabled nastavení
# 4. Stejné kategorie jako ve formulářích

# Pro aplikaci změn:
# 1. Otevři main.py
# 2. Najdi příslušné funkce podle čísla řádků
# 3. Nahraď jejich obsah kódem z tohoto patche
# 4. Ulož soubor
# 5. Restartuj aplikaci

# NEBO použij automatický patch tool (pokud existuje):
# python apply_unified_cards_patch.py
