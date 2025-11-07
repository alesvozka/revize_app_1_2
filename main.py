from fastapi import FastAPI, Request, Depends
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from starlette.middleware.sessions import SessionMiddleware
import os

from database import engine, get_db, Base
from models import *

# Create all tables
Base.metadata.create_all(bind=engine)

# Initialize default user if not exists
def init_default_user():
    """Vytvoří defaultního uživatele pokud neexistuje"""
    db = next(get_db())
    try:
        existing_user = db.query(User).filter(User.user_id == 1).first()
        if not existing_user:
            user = User(
                user_id=1,
                username="admin",
                email="admin@revize-app.cz",
                password_hash="placeholder_hash"
            )
            db.add(user)
            db.commit()
            print("✅ Vytvořen defaultní uživatel: admin (ID=1)")
        else:
            print("ℹ️  Defaultní uživatel již existuje")
    except Exception as e:
        print(f"⚠️  Chyba při vytváření defaultního uživatele: {e}")
        db.rollback()
    finally:
        db.close()

# Initialize FastAPI app
app = FastAPI(title="Revize App")

# Create default user on startup
@app.on_event("startup")
async def startup_event():
    init_default_user()

# Add session middleware
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)

# Setup templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set default user (for now, without authentication)
def get_current_user(request: Request):
    """Get current user from session. For now, returns default user_id=1"""
    user_id = request.session.get("user_id", 1)
    return user_id


# Define which fields can have dropdowns for each entity
def get_dropdown_configurable_fields():
    """Returns dictionary of entities and their dropdown-configurable fields"""
    return {
        "switchboard": {
            "switchboard_type": "Typ rozváděče",
            "switchboard_ip_rating": "Stupeň krytí (IP)",
            "switchboard_impact_protection": "Mechanická odolnost (IK)",
            "switchboard_protection_class": "Třída ochrany",
            "switchboard_manufacturer": "Výrobce rozváděče",
            "switchboard_enclosure_manufacturer": "Výrobce skříně",
            "switchboard_enclosure_installation_method": "Způsob instalace skříně",
            "switchboard_superior_circuit_breaker_trip_characteristic": "Vypínací charakteristika nadřazeného jističe",
            "switchboard_superior_circuit_breaker_manufacturer": "Výrobce nadřazeného jističe",
            "switchboard_cable": "Typ kabelu",
            "switchboard_cable_installation_method": "Způsob uložení kabelu",
        },
        "device": {
            "switchboard_device_type": "Typ přístroje",
            "switchboard_device_manufacturer": "Výrobce přístroje",
            "switchboard_device_trip_characteristic": "Vypínací charakteristika",
        },
        "circuit": {
            "circuit_cable": "Typ kabelu",
            "circuit_cable_installation_method": "Způsob uložení kabelu",
        },
        "terminal_device": {
            "terminal_device_type": "Typ koncového zařízení",
            "terminal_device_manufacturer": "Výrobce koncového zařízení",
            "terminal_device_ip_rating": "Stupeň krytí (IP)",
            "terminal_device_protection_class": "Třída ochrany",
            "terminal_device_installation_method": "Způsob instalace",
        },
    }


def get_field_dropdown_config(entity_type: str, db: Session):
    """Get dropdown configuration for all fields of an entity type
    
    Returns:
        dict: {field_name: {'enabled': bool, 'category': str or None}}
    """
    configs = db.query(DropdownConfig).filter(
        DropdownConfig.entity_type == entity_type
    ).all()
    
    result = {}
    for config in configs:
        result[config.field_name] = {
            'enabled': config.dropdown_enabled,
            'category': config.dropdown_category
        }
    
    return result


# Root endpoint - Dashboard
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Fetch user's revisions
    revisions = db.query(Revision).filter(Revision.user_id == user_id).order_by(Revision.revision_date_of_creation.desc()).all()
    
    # Calculate statistics
    total_revisions = len(revisions)
    active_revisions = sum(1 for r in revisions if r.revision_end_date is None)
    completed_revisions = sum(1 for r in revisions if r.revision_end_date is not None)
    
    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "user_id": user_id,
        "revisions": revisions,
        "total_revisions": total_revisions,
        "active_revisions": active_revisions,
        "completed_revisions": completed_revisions
    })


# Health check endpoint
@app.get("/health")
async def health_check():
    return {"status": "ok"}


# REVISION CRUD ENDPOINTS

# Create - Show form
@app.get("/revision/create", response_class=HTMLResponse)
async def revision_create_form(request: Request):
    user_id = get_current_user(request)
    return templates.TemplateResponse("revision_form.html", {
        "request": request,
        "user_id": user_id,
        "revision": None
    })


# Create - Save new revision
@app.post("/revision/create")
async def revision_create(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    form_data = await request.form()
    
    # Helper function to convert empty strings to None
    def get_value(key, convert_type=None):
        value = form_data.get(key, "").strip()
        if not value:
            return None
        if convert_type == int:
            return int(value) if value else None
        if convert_type == float:
            return float(value) if value else None
        return value
    
    # Create new revision
    new_revision = Revision(
        user_id=user_id,
        revision_code=get_value("revision_code"),
        revision_name=get_value("revision_name"),
        revision_owner=get_value("revision_owner"),
        revision_client=get_value("revision_client"),
        revision_address=get_value("revision_address"),
        revision_description=get_value("revision_description"),
        revision_type=get_value("revision_type"),
        revision_date_of_previous_revision=get_value("revision_date_of_previous_revision"),
        revision_start_date=get_value("revision_start_date"),
        revision_end_date=get_value("revision_end_date"),
        revision_date_of_creation=get_value("revision_date_of_creation"),
        revision_recommended_date_for_next_revision=get_value("revision_recommended_date_for_next_revision"),
        revision_number_of_copies_technician=get_value("revision_number_of_copies_technician", int),
        revision_number_of_copies_owner=get_value("revision_number_of_copies_owner", int),
        revision_number_of_copies_contractor=get_value("revision_number_of_copies_contractor", int),
        revision_number_of_copies_client=get_value("revision_number_of_copies_client", int),
        revision_attachment=get_value("revision_attachment"),
        revision_attachment_submitter=get_value("revision_attachment_submitter"),
        revision_attachment_producer=get_value("revision_attachment_producer"),
        revision_attachment_date_of_creation=get_value("revision_attachment_date_of_creation"),
        revision_technician=get_value("revision_technician"),
        revision_certificate_number=get_value("revision_certificate_number"),
        revision_authorization_number=get_value("revision_authorization_number"),
        revision_project_documentation=get_value("revision_project_documentation"),
        revision_contractor=get_value("revision_contractor"),
        revision_short_description=get_value("revision_short_description"),
        revision_measuring_instrument_manufacturer_type=get_value("revision_measuring_instrument_manufacturer_type"),
        revision_measuring_instrument_serial_number=get_value("revision_measuring_instrument_serial_number"),
        revision_measuring_instrument_calibration=get_value("revision_measuring_instrument_calibration"),
        revision_measuring_instrument_calibration_validity=get_value("revision_measuring_instrument_calibration_validity"),
        revision_overall_assessment=get_value("revision_overall_assessment")
    )
    
    db.add(new_revision)
    db.commit()
    db.refresh(new_revision)
    
    # Redirect to revision detail
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/revision/{new_revision.revision_id}", status_code=303)


# Read - Show detail
@app.get("/revision/{revision_id}", response_class=HTMLResponse)
async def revision_detail(revision_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    revision = db.query(Revision).filter(
        Revision.revision_id == revision_id,
        Revision.user_id == user_id
    ).first()
    
    if not revision:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    return templates.TemplateResponse("revision_detail.html", {
        "request": request,
        "user_id": user_id,
        "revision": revision
    })


# Update - Show edit form
@app.get("/revision/{revision_id}/edit", response_class=HTMLResponse)
async def revision_edit_form(revision_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    revision = db.query(Revision).filter(
        Revision.revision_id == revision_id,
        Revision.user_id == user_id
    ).first()
    
    if not revision:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    return templates.TemplateResponse("revision_form.html", {
        "request": request,
        "user_id": user_id,
        "revision": revision
    })


# Update - Save changes
@app.post("/revision/{revision_id}/update")
async def revision_update(revision_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    revision = db.query(Revision).filter(
        Revision.revision_id == revision_id,
        Revision.user_id == user_id
    ).first()
    
    if not revision:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    form_data = await request.form()
    
    # Helper function to convert empty strings to None
    def get_value(key, convert_type=None):
        value = form_data.get(key, "").strip()
        if not value:
            return None
        if convert_type == int:
            return int(value) if value else None
        if convert_type == float:
            return float(value) if value else None
        return value
    
    # Update revision fields
    revision.revision_code = get_value("revision_code")
    revision.revision_name = get_value("revision_name")
    revision.revision_owner = get_value("revision_owner")
    revision.revision_client = get_value("revision_client")
    revision.revision_address = get_value("revision_address")
    revision.revision_description = get_value("revision_description")
    revision.revision_type = get_value("revision_type")
    revision.revision_date_of_previous_revision = get_value("revision_date_of_previous_revision")
    revision.revision_start_date = get_value("revision_start_date")
    revision.revision_end_date = get_value("revision_end_date")
    revision.revision_date_of_creation = get_value("revision_date_of_creation")
    revision.revision_recommended_date_for_next_revision = get_value("revision_recommended_date_for_next_revision")
    revision.revision_number_of_copies_technician = get_value("revision_number_of_copies_technician", int)
    revision.revision_number_of_copies_owner = get_value("revision_number_of_copies_owner", int)
    revision.revision_number_of_copies_contractor = get_value("revision_number_of_copies_contractor", int)
    revision.revision_number_of_copies_client = get_value("revision_number_of_copies_client", int)
    revision.revision_attachment = get_value("revision_attachment")
    revision.revision_attachment_submitter = get_value("revision_attachment_submitter")
    revision.revision_attachment_producer = get_value("revision_attachment_producer")
    revision.revision_attachment_date_of_creation = get_value("revision_attachment_date_of_creation")
    revision.revision_technician = get_value("revision_technician")
    revision.revision_certificate_number = get_value("revision_certificate_number")
    revision.revision_authorization_number = get_value("revision_authorization_number")
    revision.revision_project_documentation = get_value("revision_project_documentation")
    revision.revision_contractor = get_value("revision_contractor")
    revision.revision_short_description = get_value("revision_short_description")
    revision.revision_measuring_instrument_manufacturer_type = get_value("revision_measuring_instrument_manufacturer_type")
    revision.revision_measuring_instrument_serial_number = get_value("revision_measuring_instrument_serial_number")
    revision.revision_measuring_instrument_calibration = get_value("revision_measuring_instrument_calibration")
    revision.revision_measuring_instrument_calibration_validity = get_value("revision_measuring_instrument_calibration_validity")
    revision.revision_overall_assessment = get_value("revision_overall_assessment")
    
    db.commit()
    
    # Redirect to revision detail
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/revision/{revision_id}", status_code=303)


# Delete
@app.post("/revision/{revision_id}/delete")
async def revision_delete(revision_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    revision = db.query(Revision).filter(
        Revision.revision_id == revision_id,
        Revision.user_id == user_id
    ).first()
    
    if revision:
        db.delete(revision)
        db.commit()
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=303)


# SWITCHBOARD CRUD ENDPOINTS

# Create - Show form
@app.get("/revision/{revision_id}/switchboard/create", response_class=HTMLResponse)
async def switchboard_create_form(revision_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    revision = db.query(Revision).filter(
        Revision.revision_id == revision_id,
        Revision.user_id == user_id
    ).first()
    
    if not revision:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    # Get dropdown configuration for switchboard
    dropdown_config = get_field_dropdown_config("switchboard", db)
    
    # Get all dropdown sources grouped by category
    categories = db.query(DropdownSource.category).distinct().all()
    dropdown_sources = {}
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    return templates.TemplateResponse("switchboard_form.html", {
        "request": request,
        "user_id": user_id,
        "revision": revision,
        "switchboard": None,
        "dropdown_config": dropdown_config,
        "dropdown_sources": dropdown_sources
    })


# Create - Save new switchboard
@app.post("/revision/{revision_id}/switchboard/create")
async def switchboard_create(revision_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    revision = db.query(Revision).filter(
        Revision.revision_id == revision_id,
        Revision.user_id == user_id
    ).first()
    
    if not revision:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    form_data = await request.form()
    
    # Helper function
    def get_value(key, convert_type=None):
        value = form_data.get(key, "").strip()
        if not value:
            return None
        if convert_type == int:
            return int(value) if value else None
        if convert_type == float:
            return float(value) if value else None
        return value
    
    # Create new switchboard
    new_switchboard = Switchboard(
        revision_id=revision_id,
        switchboard_name=get_value("switchboard_name"),
        switchboard_description=get_value("switchboard_description"),
        switchboard_location=get_value("switchboard_location"),
        switchboard_order=get_value("switchboard_order", int),
        switchboard_type=get_value("switchboard_type"),
        switchboard_serial_number=get_value("switchboard_serial_number"),
        switchboard_production_date=get_value("switchboard_production_date"),
        switchboard_ip_rating=get_value("switchboard_ip_rating"),
        switchboard_impact_protection=get_value("switchboard_impact_protection"),
        switchboard_protection_class=get_value("switchboard_protection_class"),
        switchboard_rated_current=get_value("switchboard_rated_current", float),
        switchboard_rated_voltage=get_value("switchboard_rated_voltage", float),
        switchboard_manufacturer=get_value("switchboard_manufacturer"),
        switchboard_manufacturer_address=get_value("switchboard_manufacturer_address"),
        switchboard_standards=get_value("switchboard_standards"),
        switchboard_enclosure_type=get_value("switchboard_enclosure_type"),
        switchboard_enclosure_manufacturer=get_value("switchboard_enclosure_manufacturer"),
        switchboard_enclosure_installation_method=get_value("switchboard_enclosure_installation_method"),
        switchboard_superior_switchboard=get_value("switchboard_superior_switchboard"),
        switchboard_superior_circuit_breaker_rated_current=get_value("switchboard_superior_circuit_breaker_rated_current", float),
        switchboard_superior_circuit_breaker_trip_characteristic=get_value("switchboard_superior_circuit_breaker_trip_characteristic"),
        switchboard_superior_circuit_breaker_manufacturer=get_value("switchboard_superior_circuit_breaker_manufacturer"),
        switchboard_superior_circuit_breaker_model=get_value("switchboard_superior_circuit_breaker_model"),
        switchboard_main_switch=get_value("switchboard_main_switch"),
        switchboard_note=get_value("switchboard_note"),
        switchboard_cable=get_value("switchboard_cable"),
        switchboard_cable_installation_method=get_value("switchboard_cable_installation_method")
    )
    
    db.add(new_switchboard)
    db.commit()
    db.refresh(new_switchboard)
    
    # Redirect to switchboard detail
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/switchboard/{new_switchboard.switchboard_id}", status_code=303)


# Read - Show detail
@app.get("/switchboard/{switchboard_id}", response_class=HTMLResponse)
async def switchboard_detail(switchboard_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    switchboard = db.query(Switchboard).join(Revision).filter(
        Switchboard.switchboard_id == switchboard_id,
        Revision.user_id == user_id
    ).first()
    
    if not switchboard:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    return templates.TemplateResponse("switchboard_detail.html", {
        "request": request,
        "user_id": user_id,
        "switchboard": switchboard
    })


# Update - Show edit form
@app.get("/switchboard/{switchboard_id}/edit", response_class=HTMLResponse)
async def switchboard_edit_form(switchboard_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    switchboard = db.query(Switchboard).join(Revision).filter(
        Switchboard.switchboard_id == switchboard_id,
        Revision.user_id == user_id
    ).first()
    
    if not switchboard:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    # Get dropdown configuration for switchboard
    dropdown_config = get_field_dropdown_config("switchboard", db)
    
    # Get all dropdown sources grouped by category
    categories = db.query(DropdownSource.category).distinct().all()
    dropdown_sources = {}
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    return templates.TemplateResponse("switchboard_form.html", {
        "request": request,
        "user_id": user_id,
        "revision": switchboard.revision,
        "switchboard": switchboard,
        "dropdown_config": dropdown_config,
        "dropdown_sources": dropdown_sources
    })


# Update - Save changes
@app.post("/switchboard/{switchboard_id}/update")
async def switchboard_update(switchboard_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    switchboard = db.query(Switchboard).join(Revision).filter(
        Switchboard.switchboard_id == switchboard_id,
        Revision.user_id == user_id
    ).first()
    
    if not switchboard:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    form_data = await request.form()
    
    # Helper function
    def get_value(key, convert_type=None):
        value = form_data.get(key, "").strip()
        if not value:
            return None
        if convert_type == int:
            return int(value) if value else None
        if convert_type == float:
            return float(value) if value else None
        return value
    
    # Update switchboard fields
    switchboard.switchboard_name = get_value("switchboard_name")
    switchboard.switchboard_description = get_value("switchboard_description")
    switchboard.switchboard_location = get_value("switchboard_location")
    switchboard.switchboard_order = get_value("switchboard_order", int)
    switchboard.switchboard_type = get_value("switchboard_type")
    switchboard.switchboard_serial_number = get_value("switchboard_serial_number")
    switchboard.switchboard_production_date = get_value("switchboard_production_date")
    switchboard.switchboard_ip_rating = get_value("switchboard_ip_rating")
    switchboard.switchboard_impact_protection = get_value("switchboard_impact_protection")
    switchboard.switchboard_protection_class = get_value("switchboard_protection_class")
    switchboard.switchboard_rated_current = get_value("switchboard_rated_current", float)
    switchboard.switchboard_rated_voltage = get_value("switchboard_rated_voltage", float)
    switchboard.switchboard_manufacturer = get_value("switchboard_manufacturer")
    switchboard.switchboard_manufacturer_address = get_value("switchboard_manufacturer_address")
    switchboard.switchboard_standards = get_value("switchboard_standards")
    switchboard.switchboard_enclosure_type = get_value("switchboard_enclosure_type")
    switchboard.switchboard_enclosure_manufacturer = get_value("switchboard_enclosure_manufacturer")
    switchboard.switchboard_enclosure_installation_method = get_value("switchboard_enclosure_installation_method")
    switchboard.switchboard_superior_switchboard = get_value("switchboard_superior_switchboard")
    switchboard.switchboard_superior_circuit_breaker_rated_current = get_value("switchboard_superior_circuit_breaker_rated_current", float)
    switchboard.switchboard_superior_circuit_breaker_trip_characteristic = get_value("switchboard_superior_circuit_breaker_trip_characteristic")
    switchboard.switchboard_superior_circuit_breaker_manufacturer = get_value("switchboard_superior_circuit_breaker_manufacturer")
    switchboard.switchboard_superior_circuit_breaker_model = get_value("switchboard_superior_circuit_breaker_model")
    switchboard.switchboard_main_switch = get_value("switchboard_main_switch")
    switchboard.switchboard_note = get_value("switchboard_note")
    switchboard.switchboard_cable = get_value("switchboard_cable")
    switchboard.switchboard_cable_installation_method = get_value("switchboard_cable_installation_method")
    
    db.commit()
    
    # Redirect to switchboard detail
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/switchboard/{switchboard_id}", status_code=303)


# Delete
@app.post("/switchboard/{switchboard_id}/delete")
async def switchboard_delete(switchboard_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    switchboard = db.query(Switchboard).join(Revision).filter(
        Switchboard.switchboard_id == switchboard_id,
        Revision.user_id == user_id
    ).first()
    
    if switchboard:
        revision_id = switchboard.revision_id
        db.delete(switchboard)
        db.commit()
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"/revision/{revision_id}", status_code=303)
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=303)


# SWITCHBOARD MEASUREMENT CRUD ENDPOINTS

# Create - Show form
@app.get("/switchboard/{switchboard_id}/measurement/create", response_class=HTMLResponse)
async def measurement_create_form(switchboard_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    switchboard = db.query(Switchboard).join(Revision).filter(
        Switchboard.switchboard_id == switchboard_id,
        Revision.user_id == user_id
    ).first()
    
    if not switchboard:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    # Check if measurement already exists (1:1 relationship)
    if switchboard.measurements:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"/switchboard/{switchboard_id}/measurement/edit", status_code=303)
    
    return templates.TemplateResponse("measurement_form.html", {
        "request": request,
        "user_id": user_id,
        "switchboard": switchboard,
        "measurement": None
    })


# Create - Save new measurement
@app.post("/switchboard/{switchboard_id}/measurement/create")
async def measurement_create(switchboard_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    switchboard = db.query(Switchboard).join(Revision).filter(
        Switchboard.switchboard_id == switchboard_id,
        Revision.user_id == user_id
    ).first()
    
    if not switchboard:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    # Check if measurement already exists
    if switchboard.measurements:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"/switchboard/{switchboard_id}", status_code=303)
    
    form_data = await request.form()
    
    # Helper function
    def get_value(key, convert_type=None):
        value = form_data.get(key, "").strip()
        if not value:
            return None
        if convert_type == float:
            return float(value) if value else None
        return value
    
    # Create new measurement
    new_measurement = SwitchboardMeasurement(
        switchboard_id=switchboard_id,
        measurements_switchboard_insulation_resistance=get_value("measurements_switchboard_insulation_resistance", float),
        measurements_switchboard_loop_impedance_min=get_value("measurements_switchboard_loop_impedance_min", float),
        measurements_switchboard_loop_impedance_max=get_value("measurements_switchboard_loop_impedance_max", float),
        measurements_switchboard_rcd_trip_time_ms=get_value("measurements_switchboard_rcd_trip_time_ms", float),
        measurements_switchboard_rcd_test_current_ma=get_value("measurements_switchboard_rcd_test_current_ma", float),
        measurements_switchboard_earth_resistance=get_value("measurements_switchboard_earth_resistance", float)
    )
    
    db.add(new_measurement)
    db.commit()
    
    # Redirect to switchboard detail
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/switchboard/{switchboard_id}", status_code=303)


# Update - Show edit form
@app.get("/switchboard/{switchboard_id}/measurement/edit", response_class=HTMLResponse)
async def measurement_edit_form(switchboard_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    switchboard = db.query(Switchboard).join(Revision).filter(
        Switchboard.switchboard_id == switchboard_id,
        Revision.user_id == user_id
    ).first()
    
    if not switchboard or not switchboard.measurements:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"/switchboard/{switchboard_id}", status_code=303)
    
    return templates.TemplateResponse("measurement_form.html", {
        "request": request,
        "user_id": user_id,
        "switchboard": switchboard,
        "measurement": switchboard.measurements
    })


# Update - Save changes
@app.post("/measurement/{measurement_id}/update")
async def measurement_update(measurement_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    measurement = db.query(SwitchboardMeasurement).join(Switchboard).join(Revision).filter(
        SwitchboardMeasurement.measurement_id == measurement_id,
        Revision.user_id == user_id
    ).first()
    
    if not measurement:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    form_data = await request.form()
    
    # Helper function
    def get_value(key, convert_type=None):
        value = form_data.get(key, "").strip()
        if not value:
            return None
        if convert_type == float:
            return float(value) if value else None
        return value
    
    # Update measurement fields
    measurement.measurements_switchboard_insulation_resistance = get_value("measurements_switchboard_insulation_resistance", float)
    measurement.measurements_switchboard_loop_impedance_min = get_value("measurements_switchboard_loop_impedance_min", float)
    measurement.measurements_switchboard_loop_impedance_max = get_value("measurements_switchboard_loop_impedance_max", float)
    measurement.measurements_switchboard_rcd_trip_time_ms = get_value("measurements_switchboard_rcd_trip_time_ms", float)
    measurement.measurements_switchboard_rcd_test_current_ma = get_value("measurements_switchboard_rcd_test_current_ma", float)
    measurement.measurements_switchboard_earth_resistance = get_value("measurements_switchboard_earth_resistance", float)
    
    db.commit()
    
    # Redirect to switchboard detail
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/switchboard/{measurement.switchboard_id}", status_code=303)


# Delete
@app.post("/measurement/{measurement_id}/delete")
async def measurement_delete(measurement_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    measurement = db.query(SwitchboardMeasurement).join(Switchboard).join(Revision).filter(
        SwitchboardMeasurement.measurement_id == measurement_id,
        Revision.user_id == user_id
    ).first()
    
    if measurement:
        switchboard_id = measurement.switchboard_id
        db.delete(measurement)
        db.commit()
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"/switchboard/{switchboard_id}", status_code=303)
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=303)


# ===== SWITCHBOARD DEVICE (PŘÍSTROJE V ROZVÁDĚČI) =====

# Create - Show form
@app.get("/switchboard/{switchboard_id}/device/create", response_class=HTMLResponse)
async def device_create_form(switchboard_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Verify ownership through switchboard -> revision
    switchboard = db.query(Switchboard).join(Revision).filter(
        Switchboard.switchboard_id == switchboard_id,
        Revision.user_id == user_id
    ).first()
    
    if not switchboard:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    # Get all devices in this switchboard for parent selection
    devices = db.query(SwitchboardDevice).filter(
        SwitchboardDevice.switchboard_id == switchboard_id
    ).order_by(SwitchboardDevice.switchboard_device_position).all()
    
    # Get dropdown configuration for device
    dropdown_config = get_field_dropdown_config("device", db)
    
    # Get all dropdown sources grouped by category
    categories = db.query(DropdownSource.category).distinct().all()
    dropdown_sources = {}
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    return templates.TemplateResponse("device_form.html", {
        "request": request,
        "user_id": user_id,
        "switchboard": switchboard,
        "device": None,
        "devices": devices,
        "dropdown_config": dropdown_config,
        "dropdown_sources": dropdown_sources
    })


# Create - Save new device
@app.post("/switchboard/{switchboard_id}/device/create")
async def device_create(switchboard_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    form_data = await request.form()
    
    # Verify ownership
    switchboard = db.query(Switchboard).join(Revision).filter(
        Switchboard.switchboard_id == switchboard_id,
        Revision.user_id == user_id
    ).first()
    
    if not switchboard:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    def get_value(key, convert_type=None):
        value = form_data.get(key, "").strip()
        if not value:
            return None
        if convert_type == int:
            return int(value) if value else None
        if convert_type == float:
            return float(value) if value else None
        return value
    
    # Create new device
    new_device = SwitchboardDevice(
        switchboard_id=switchboard_id,
        parent_device_id=get_value("parent_device_id", int),
        switchboard_device_position=get_value("switchboard_device_position"),
        switchboard_device_type=get_value("switchboard_device_type"),
        switchboard_device_manufacturer=get_value("switchboard_device_manufacturer"),
        switchboard_device_model=get_value("switchboard_device_model"),
        switchboard_device_trip_characteristic=get_value("switchboard_device_trip_characteristic"),
        switchboard_device_rated_current=get_value("switchboard_device_rated_current", float),
        switchboard_device_residual_current_ma=get_value("switchboard_device_residual_current_ma", float),
        switchboard_device_sub_devices=get_value("switchboard_device_sub_devices"),
        switchboard_device_poles=get_value("switchboard_device_poles", int),
        switchboard_device_module_width=get_value("switchboard_device_module_width", float)
    )
    
    db.add(new_device)
    db.commit()
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/switchboard/{switchboard_id}", status_code=303)


# Update - Show form
@app.get("/device/{device_id}/edit", response_class=HTMLResponse)
async def device_edit_form(device_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Verify ownership through device -> switchboard -> revision
    device = db.query(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        SwitchboardDevice.device_id == device_id,
        Revision.user_id == user_id
    ).first()
    
    if not device:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    # Get all devices in this switchboard for parent selection (exclude self and descendants)
    devices = db.query(SwitchboardDevice).filter(
        SwitchboardDevice.switchboard_id == device.switchboard_id,
        SwitchboardDevice.device_id != device_id
    ).order_by(SwitchboardDevice.switchboard_device_position).all()
    
    # Get dropdown configuration for device
    dropdown_config = get_field_dropdown_config("device", db)
    
    # Get all dropdown sources grouped by category
    categories = db.query(DropdownSource.category).distinct().all()
    dropdown_sources = {}
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    return templates.TemplateResponse("device_form.html", {
        "request": request,
        "user_id": user_id,
        "switchboard": device.switchboard,
        "device": device,
        "devices": devices,
        "dropdown_config": dropdown_config,
        "dropdown_sources": dropdown_sources
    })


# Update - Save
@app.post("/device/{device_id}/update")
async def device_update(device_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    form_data = await request.form()
    
    # Verify ownership
    device = db.query(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        SwitchboardDevice.device_id == device_id,
        Revision.user_id == user_id
    ).first()
    
    if not device:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    def get_value(key, convert_type=None):
        value = form_data.get(key, "").strip()
        if not value:
            return None
        if convert_type == int:
            return int(value) if value else None
        if convert_type == float:
            return float(value) if value else None
        return value
    
    # Update device fields
    device.parent_device_id = get_value("parent_device_id", int)
    device.switchboard_device_position = get_value("switchboard_device_position")
    device.switchboard_device_type = get_value("switchboard_device_type")
    device.switchboard_device_manufacturer = get_value("switchboard_device_manufacturer")
    device.switchboard_device_model = get_value("switchboard_device_model")
    device.switchboard_device_trip_characteristic = get_value("switchboard_device_trip_characteristic")
    device.switchboard_device_rated_current = get_value("switchboard_device_rated_current", float)
    device.switchboard_device_residual_current_ma = get_value("switchboard_device_residual_current_ma", float)
    device.switchboard_device_sub_devices = get_value("switchboard_device_sub_devices")
    device.switchboard_device_poles = get_value("switchboard_device_poles", int)
    device.switchboard_device_module_width = get_value("switchboard_device_module_width", float)
    
    db.commit()
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/switchboard/{device.switchboard_id}", status_code=303)


# Delete
@app.post("/device/{device_id}/delete")
async def device_delete(device_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Verify ownership
    device = db.query(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        SwitchboardDevice.device_id == device_id,
        Revision.user_id == user_id
    ).first()
    
    if device:
        switchboard_id = device.switchboard_id
        # SQLAlchemy will handle cascade delete of child devices due to self-referencing relationship
        db.delete(device)
        db.commit()
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"/switchboard/{switchboard_id}", status_code=303)
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=303)


# ============================================================================
# CIRCUIT CRUD
# ============================================================================

# CREATE - Show form
@app.get("/device/{device_id}/circuit/create", response_class=HTMLResponse)
async def circuit_create_form(device_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Verify device ownership through switchboard → revision
    device = db.query(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        SwitchboardDevice.device_id == device_id,
        Revision.user_id == user_id
    ).first()
    
    if not device:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    # Get dropdown configuration for circuit
    dropdown_config = get_field_dropdown_config("circuit", db)
    
    # Get all dropdown sources grouped by category
    categories = db.query(DropdownSource.category).distinct().all()
    dropdown_sources = {}
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    return templates.TemplateResponse("circuit_form.html", {
        "request": request,
        "device": device,
        "circuit": None,
        "is_edit": False,
        "dropdown_config": dropdown_config,
        "dropdown_sources": dropdown_sources
    })


# CREATE - Process form
@app.post("/device/{device_id}/circuit/create")
async def circuit_create(device_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Verify device ownership
    device = db.query(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        SwitchboardDevice.device_id == device_id,
        Revision.user_id == user_id
    ).first()
    
    if not device:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    form_data = await request.form()
    
    def get_value(key, type_cast=None):
        value = form_data.get(key, "").strip()
        if not value:
            return None
        if type_cast == int:
            try:
                return int(value)
            except ValueError:
                return None
        elif type_cast == float:
            try:
                return float(value)
            except ValueError:
                return None
        return value
    
    # Create circuit
    new_circuit = Circuit(
        device_id=device_id,
        circuit_number=get_value("circuit_number"),
        circuit_room=get_value("circuit_room"),
        circuit_description=get_value("circuit_description"),
        circuit_description_from_switchboard=get_value("circuit_description_from_switchboard"),
        circuit_number_of_outlets=get_value("circuit_number_of_outlets", int),
        circuit_cable_termination=get_value("circuit_cable_termination"),
        circuit_cable=get_value("circuit_cable"),
        circuit_cable_installation_method=get_value("circuit_cable_installation_method")
    )
    
    db.add(new_circuit)
    db.commit()
    db.refresh(new_circuit)
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/circuit/{new_circuit.circuit_id}", status_code=303)


# READ - Circuit detail
@app.get("/circuit/{circuit_id}", response_class=HTMLResponse)
async def circuit_detail(circuit_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Get circuit with device, switchboard, and revision
    circuit = db.query(Circuit).join(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        Circuit.circuit_id == circuit_id,
        Revision.user_id == user_id
    ).first()
    
    if not circuit:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    # Get measurement if exists (1:1 relationship)
    measurement = db.query(CircuitMeasurement).filter(
        CircuitMeasurement.circuit_id == circuit_id
    ).first()
    
    # Get terminal devices (1:N relationship)
    terminal_devices = db.query(TerminalDevice).filter(
        TerminalDevice.circuit_id == circuit_id
    ).all()
    
    return templates.TemplateResponse("circuit_detail.html", {
        "request": request,
        "circuit": circuit,
        "measurement": measurement,
        "terminal_devices": terminal_devices
    })


# UPDATE - Show edit form
@app.get("/circuit/{circuit_id}/edit", response_class=HTMLResponse)
async def circuit_edit_form(circuit_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Get circuit with verification
    circuit = db.query(Circuit).join(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        Circuit.circuit_id == circuit_id,
        Revision.user_id == user_id
    ).first()
    
    if not circuit:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    # Get dropdown configuration for circuit
    dropdown_config = get_field_dropdown_config("circuit", db)
    
    # Get all dropdown sources grouped by category
    categories = db.query(DropdownSource.category).distinct().all()
    dropdown_sources = {}
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    return templates.TemplateResponse("circuit_form.html", {
        "request": request,
        "device": circuit.device,
        "circuit": circuit,
        "is_edit": True,
        "dropdown_config": dropdown_config,
        "dropdown_sources": dropdown_sources
    })


# UPDATE - Process form
@app.post("/circuit/{circuit_id}/update")
async def circuit_update(circuit_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Get circuit with verification
    circuit = db.query(Circuit).join(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        Circuit.circuit_id == circuit_id,
        Revision.user_id == user_id
    ).first()
    
    if not circuit:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    form_data = await request.form()
    
    def get_value(key, type_cast=None):
        value = form_data.get(key, "").strip()
        if not value:
            return None
        if type_cast == int:
            try:
                return int(value)
            except ValueError:
                return None
        elif type_cast == float:
            try:
                return float(value)
            except ValueError:
                return None
        return value
    
    # Update circuit fields
    circuit.circuit_number = get_value("circuit_number")
    circuit.circuit_room = get_value("circuit_room")
    circuit.circuit_description = get_value("circuit_description")
    circuit.circuit_description_from_switchboard = get_value("circuit_description_from_switchboard")
    circuit.circuit_number_of_outlets = get_value("circuit_number_of_outlets", int)
    circuit.circuit_cable_termination = get_value("circuit_cable_termination")
    circuit.circuit_cable = get_value("circuit_cable")
    circuit.circuit_cable_installation_method = get_value("circuit_cable_installation_method")
    
    db.commit()
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/circuit/{circuit_id}", status_code=303)


# DELETE
@app.post("/circuit/{circuit_id}/delete")
async def circuit_delete(circuit_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Verify ownership
    circuit = db.query(Circuit).join(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        Circuit.circuit_id == circuit_id,
        Revision.user_id == user_id
    ).first()
    
    if circuit:
        device_id = circuit.device_id
        # SQLAlchemy will handle cascade delete of measurements and terminal devices
        db.delete(circuit)
        db.commit()
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"/device/{device_id}", status_code=303)
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=303)


# ============================================================================
# CIRCUIT MEASUREMENT CRUD
# ============================================================================

# CREATE - Show form
@app.get("/circuit/{circuit_id}/measurement/create", response_class=HTMLResponse)
async def circuit_measurement_create_form(circuit_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Verify circuit ownership
    circuit = db.query(Circuit).join(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        Circuit.circuit_id == circuit_id,
        Revision.user_id == user_id
    ).first()
    
    if not circuit:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    # Check if measurement already exists (1:1)
    existing = db.query(CircuitMeasurement).filter(
        CircuitMeasurement.circuit_id == circuit_id
    ).first()
    
    if existing:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"/circuit/{circuit_id}/measurement/edit", status_code=303)
    
    return templates.TemplateResponse("circuit_measurement_form.html", {
        "request": request,
        "circuit": circuit,
        "measurement": None,
        "is_edit": False
    })


# CREATE - Process form
@app.post("/circuit/{circuit_id}/measurement/create")
async def circuit_measurement_create(circuit_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Verify circuit ownership
    circuit = db.query(Circuit).join(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        Circuit.circuit_id == circuit_id,
        Revision.user_id == user_id
    ).first()
    
    if not circuit:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    form_data = await request.form()
    
    def get_value(key, type_cast=None):
        value = form_data.get(key, "").strip()
        if not value:
            return None
        if type_cast == float:
            try:
                return float(value)
            except ValueError:
                return None
        return value
    
    # Create measurement
    new_measurement = CircuitMeasurement(
        circuit_id=circuit_id,
        measurements_circuit_insulation_resistance=get_value("measurements_circuit_insulation_resistance", float),
        measurements_circuit_loop_impedance_min=get_value("measurements_circuit_loop_impedance_min", float),
        measurements_circuit_loop_impedance_max=get_value("measurements_circuit_loop_impedance_max", float),
        measurements_circuit_rcd_trip_time_ms=get_value("measurements_circuit_rcd_trip_time_ms", float),
        measurements_circuit_rcd_test_current_ma=get_value("measurements_circuit_rcd_test_current_ma", float),
        measurements_circuit_earth_resistance=get_value("measurements_circuit_earth_resistance", float),
        measurements_circuit_continuity=get_value("measurements_circuit_continuity", float),
        measurements_circuit_order_of_phases=get_value("measurements_circuit_order_of_phases")
    )
    
    db.add(new_measurement)
    db.commit()
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/circuit/{circuit_id}", status_code=303)


# UPDATE - Show edit form
@app.get("/circuit/{circuit_id}/measurement/edit", response_class=HTMLResponse)
async def circuit_measurement_edit_form(circuit_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Verify circuit ownership
    circuit = db.query(Circuit).join(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        Circuit.circuit_id == circuit_id,
        Revision.user_id == user_id
    ).first()
    
    if not circuit:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    # Get measurement
    measurement = db.query(CircuitMeasurement).filter(
        CircuitMeasurement.circuit_id == circuit_id
    ).first()
    
    if not measurement:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"/circuit/{circuit_id}/measurement/create", status_code=303)
    
    return templates.TemplateResponse("circuit_measurement_form.html", {
        "request": request,
        "circuit": circuit,
        "measurement": measurement,
        "is_edit": True
    })


# UPDATE - Process form
@app.post("/circuit_measurement/{measurement_id}/update")
async def circuit_measurement_update(measurement_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Verify measurement ownership
    measurement = db.query(CircuitMeasurement).join(Circuit).join(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        CircuitMeasurement.measurement_id == measurement_id,
        Revision.user_id == user_id
    ).first()
    
    if not measurement:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    form_data = await request.form()
    
    def get_value(key, type_cast=None):
        value = form_data.get(key, "").strip()
        if not value:
            return None
        if type_cast == float:
            try:
                return float(value)
            except ValueError:
                return None
        return value
    
    # Update measurement fields
    measurement.measurements_circuit_insulation_resistance = get_value("measurements_circuit_insulation_resistance", float)
    measurement.measurements_circuit_loop_impedance_min = get_value("measurements_circuit_loop_impedance_min", float)
    measurement.measurements_circuit_loop_impedance_max = get_value("measurements_circuit_loop_impedance_max", float)
    measurement.measurements_circuit_rcd_trip_time_ms = get_value("measurements_circuit_rcd_trip_time_ms", float)
    measurement.measurements_circuit_rcd_test_current_ma = get_value("measurements_circuit_rcd_test_current_ma", float)
    measurement.measurements_circuit_earth_resistance = get_value("measurements_circuit_earth_resistance", float)
    measurement.measurements_circuit_continuity = get_value("measurements_circuit_continuity", float)
    measurement.measurements_circuit_order_of_phases = get_value("measurements_circuit_order_of_phases")
    
    db.commit()
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/circuit/{measurement.circuit_id}", status_code=303)


# DELETE
@app.post("/circuit_measurement/{measurement_id}/delete")
async def circuit_measurement_delete(measurement_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Verify ownership
    measurement = db.query(CircuitMeasurement).join(Circuit).join(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        CircuitMeasurement.measurement_id == measurement_id,
        Revision.user_id == user_id
    ).first()
    
    if measurement:
        circuit_id = measurement.circuit_id
        db.delete(measurement)
        db.commit()
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"/circuit/{circuit_id}", status_code=303)
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=303)


# ============================================================================
# DEVICE DETAIL (for showing circuits)
# ============================================================================

@app.get("/device/{device_id}", response_class=HTMLResponse)
async def device_detail(device_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Get device with switchboard and revision
    device = db.query(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        SwitchboardDevice.device_id == device_id,
        Revision.user_id == user_id
    ).first()
    
    if not device:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    # Get circuits for this device
    circuits = db.query(Circuit).filter(
        Circuit.device_id == device_id
    ).all()
    
    return templates.TemplateResponse("device_detail.html", {
        "request": request,
        "device": device,
        "circuits": circuits
    })


# ============================================================================
# TERMINAL DEVICE CRUD
# ============================================================================

# CREATE - Show form
@app.get("/circuit/{circuit_id}/terminal/create", response_class=HTMLResponse)
async def terminal_device_create_form(circuit_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Verify circuit ownership through device → switchboard → revision
    circuit = db.query(Circuit).join(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        Circuit.circuit_id == circuit_id,
        Revision.user_id == user_id
    ).first()
    
    if not circuit:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    # Get dropdown configuration for terminal_device
    dropdown_config = get_field_dropdown_config("terminal_device", db)
    
    # Get all dropdown sources grouped by category
    categories = db.query(DropdownSource.category).distinct().all()
    dropdown_sources = {}
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    return templates.TemplateResponse("terminal_device_form.html", {
        "request": request,
        "circuit": circuit,
        "terminal_device": None,
        "is_edit": False,
        "dropdown_config": dropdown_config,
        "dropdown_sources": dropdown_sources
    })


# CREATE - Process form
@app.post("/circuit/{circuit_id}/terminal/create")
async def terminal_device_create(circuit_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Verify circuit ownership
    circuit = db.query(Circuit).join(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        Circuit.circuit_id == circuit_id,
        Revision.user_id == user_id
    ).first()
    
    if not circuit:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    form_data = await request.form()
    
    def get_value(key, type_cast=None):
        value = form_data.get(key, "").strip()
        if not value:
            return None
        if type_cast == float:
            try:
                return float(value)
            except ValueError:
                return None
        return value
    
    # Create terminal device
    new_terminal = TerminalDevice(
        circuit_id=circuit_id,
        terminal_device_type=get_value("terminal_device_type"),
        terminal_device_manufacturer=get_value("terminal_device_manufacturer"),
        terminal_device_model=get_value("terminal_device_model"),
        terminal_device_marking=get_value("terminal_device_marking"),
        terminal_device_power=get_value("terminal_device_power", float),
        terminal_device_ip_rating=get_value("terminal_device_ip_rating"),
        terminal_device_protection_class=get_value("terminal_device_protection_class"),
        terminal_device_serial_number=get_value("terminal_device_serial_number"),
        terminal_device_supply_type=get_value("terminal_device_supply_type"),
        terminal_device_installation_method=get_value("terminal_device_installation_method")
    )
    
    db.add(new_terminal)
    db.commit()
    db.refresh(new_terminal)
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/circuit/{circuit_id}", status_code=303)


# READ - Terminal device detail
@app.get("/terminal/{terminal_device_id}", response_class=HTMLResponse)
async def terminal_device_detail(terminal_device_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Get terminal device with circuit, device, switchboard, and revision
    terminal = db.query(TerminalDevice).join(Circuit).join(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        TerminalDevice.terminal_device_id == terminal_device_id,
        Revision.user_id == user_id
    ).first()
    
    if not terminal:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    return templates.TemplateResponse("terminal_device_detail.html", {
        "request": request,
        "terminal": terminal
    })


# UPDATE - Show edit form
@app.get("/terminal/{terminal_device_id}/edit", response_class=HTMLResponse)
async def terminal_device_edit_form(terminal_device_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Get terminal device with verification
    terminal = db.query(TerminalDevice).join(Circuit).join(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        TerminalDevice.terminal_device_id == terminal_device_id,
        Revision.user_id == user_id
    ).first()
    
    if not terminal:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    # Get dropdown configuration for terminal_device
    dropdown_config = get_field_dropdown_config("terminal_device", db)
    
    # Get all dropdown sources grouped by category
    categories = db.query(DropdownSource.category).distinct().all()
    dropdown_sources = {}
    for cat in categories:
        category = cat[0]
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    return templates.TemplateResponse("terminal_device_form.html", {
        "request": request,
        "circuit": terminal.circuit,
        "terminal_device": terminal,
        "is_edit": True,
        "dropdown_config": dropdown_config,
        "dropdown_sources": dropdown_sources
    })


# UPDATE - Process form
@app.post("/terminal/{terminal_device_id}/update")
async def terminal_device_update(terminal_device_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Get terminal device with verification
    terminal = db.query(TerminalDevice).join(Circuit).join(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        TerminalDevice.terminal_device_id == terminal_device_id,
        Revision.user_id == user_id
    ).first()
    
    if not terminal:
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url="/", status_code=303)
    
    form_data = await request.form()
    
    def get_value(key, type_cast=None):
        value = form_data.get(key, "").strip()
        if not value:
            return None
        if type_cast == float:
            try:
                return float(value)
            except ValueError:
                return None
        return value
    
    # Update terminal device fields
    terminal.terminal_device_type = get_value("terminal_device_type")
    terminal.terminal_device_manufacturer = get_value("terminal_device_manufacturer")
    terminal.terminal_device_model = get_value("terminal_device_model")
    terminal.terminal_device_marking = get_value("terminal_device_marking")
    terminal.terminal_device_power = get_value("terminal_device_power", float)
    terminal.terminal_device_ip_rating = get_value("terminal_device_ip_rating")
    terminal.terminal_device_protection_class = get_value("terminal_device_protection_class")
    terminal.terminal_device_serial_number = get_value("terminal_device_serial_number")
    terminal.terminal_device_supply_type = get_value("terminal_device_supply_type")
    terminal.terminal_device_installation_method = get_value("terminal_device_installation_method")
    
    db.commit()
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url=f"/circuit/{terminal.circuit_id}", status_code=303)


# DELETE
@app.post("/terminal/{terminal_device_id}/delete")
async def terminal_device_delete(terminal_device_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Verify ownership
    terminal = db.query(TerminalDevice).join(Circuit).join(SwitchboardDevice).join(Switchboard).join(Revision).filter(
        TerminalDevice.terminal_device_id == terminal_device_id,
        Revision.user_id == user_id
    ).first()
    
    if terminal:
        circuit_id = terminal.circuit_id
        db.delete(terminal)
        db.commit()
        from fastapi.responses import RedirectResponse
        return RedirectResponse(url=f"/circuit/{circuit_id}", status_code=303)
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/", status_code=303)


# ============================================================================
# DROPDOWN SYSTEM & SETTINGS
# ============================================================================

# Settings page - Dropdown management
@app.get("/settings", response_class=HTMLResponse)
async def settings_page(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    # Get all dropdown categories (distinct)
    categories = db.query(DropdownSource.category).distinct().order_by(DropdownSource.category).all()
    categories = [cat[0] for cat in categories]
    
    # Get all dropdown sources grouped by category
    dropdown_sources = {}
    for category in categories:
        sources = db.query(DropdownSource).filter(
            DropdownSource.category == category
        ).order_by(DropdownSource.display_order, DropdownSource.value).all()
        dropdown_sources[category] = sources
    
    # Get dropdown configurations
    dropdown_configs = db.query(DropdownConfig).all()
    
    # Create dict for easy lookup of existing configs
    configs_dict = {}
    for config in dropdown_configs:
        key = f"{config.entity_type}_{config.field_name}"
        configs_dict[key] = config
    
    # Get configurable fields
    configurable_fields = get_dropdown_configurable_fields()
    
    return templates.TemplateResponse("settings.html", {
        "request": request,
        "categories": categories,
        "dropdown_sources": dropdown_sources,
        "dropdown_configs": dropdown_configs,
        "configs_dict": configs_dict,
        "configurable_fields": configurable_fields
    })


# Add new dropdown category
@app.post("/settings/dropdown/category/create")
async def dropdown_category_create(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    form_data = await request.form()
    
    category = form_data.get("category", "").strip()
    
    if category:
        # Check if category already exists
        existing = db.query(DropdownSource).filter(DropdownSource.category == category).first()
        if not existing:
            # Create first item in new category
            new_source = DropdownSource(
                category=category,
                value="Nová hodnota",
                display_order=0
            )
            db.add(new_source)
            db.commit()
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/settings", status_code=303)


# Add new dropdown value to existing category
@app.post("/settings/dropdown/value/create")
async def dropdown_value_create(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    form_data = await request.form()
    
    category = form_data.get("category", "").strip()
    value = form_data.get("value", "").strip()
    
    if category and value:
        # Get max display_order for this category
        max_order = db.query(func.max(DropdownSource.display_order)).filter(
            DropdownSource.category == category
        ).scalar() or 0
        
        new_source = DropdownSource(
            category=category,
            value=value,
            display_order=max_order + 1
        )
        db.add(new_source)
        db.commit()
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/settings", status_code=303)


# Update dropdown value
@app.post("/settings/dropdown/value/{value_id}/update")
async def dropdown_value_update(value_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    form_data = await request.form()
    
    source = db.query(DropdownSource).filter(DropdownSource.id == value_id).first()
    if source:
        new_value = form_data.get("value", "").strip()
        if new_value:
            source.value = new_value
            db.commit()
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/settings", status_code=303)


# Delete dropdown value
@app.post("/settings/dropdown/value/{value_id}/delete")
async def dropdown_value_delete(value_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    source = db.query(DropdownSource).filter(DropdownSource.id == value_id).first()
    if source:
        db.delete(source)
        db.commit()
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/settings", status_code=303)


# Move dropdown value up
@app.post("/settings/dropdown/value/{value_id}/move-up")
async def dropdown_value_move_up(value_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    source = db.query(DropdownSource).filter(DropdownSource.id == value_id).first()
    if source and source.display_order > 0:
        # Find item with previous order
        prev_source = db.query(DropdownSource).filter(
            DropdownSource.category == source.category,
            DropdownSource.display_order == source.display_order - 1
        ).first()
        
        if prev_source:
            # Swap orders
            source.display_order, prev_source.display_order = prev_source.display_order, source.display_order
            db.commit()
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/settings", status_code=303)


# Move dropdown value down
@app.post("/settings/dropdown/value/{value_id}/move-down")
async def dropdown_value_move_down(value_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    
    source = db.query(DropdownSource).filter(DropdownSource.id == value_id).first()
    if source:
        # Find item with next order
        next_source = db.query(DropdownSource).filter(
            DropdownSource.category == source.category,
            DropdownSource.display_order == source.display_order + 1
        ).first()
        
        if next_source:
            # Swap orders
            source.display_order, next_source.display_order = next_source.display_order, source.display_order
            db.commit()
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/settings", status_code=303)


# HTMX endpoint - Get dropdown values for a category (for inline widget)
@app.get("/api/dropdown/{category}")
async def get_dropdown_values(category: str, db: Session = Depends(get_db)):
    sources = db.query(DropdownSource).filter(
        DropdownSource.category == category
    ).order_by(DropdownSource.display_order, DropdownSource.value).all()
    
    return {"values": [{"id": s.id, "value": s.value} for s in sources]}


# HTMX endpoint - Add new value to dropdown (inline from form)
@app.post("/api/dropdown/{category}/add")
async def add_dropdown_value_inline(category: str, request: Request, db: Session = Depends(get_db)):
    form_data = await request.form()
    value = form_data.get("value", "").strip()
    
    if value:
        # Get max display_order for this category
        max_order = db.query(func.max(DropdownSource.display_order)).filter(
            DropdownSource.category == category
        ).scalar() or 0
        
        new_source = DropdownSource(
            category=category,
            value=value,
            display_order=max_order + 1
        )
        db.add(new_source)
        db.commit()
        db.refresh(new_source)
        
        return {"success": True, "id": new_source.id, "value": new_source.value}
    
    return {"success": False, "error": "Value is required"}


# Update dropdown configuration
@app.post("/settings/dropdown-config/update")
async def dropdown_config_update(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user(request)
    form_data = await request.form()
    
    entity_type = form_data.get("entity_type", "").strip()
    field_name = form_data.get("field_name", "").strip()
    dropdown_enabled = form_data.get("dropdown_enabled") == "on"
    dropdown_category = form_data.get("dropdown_category", "").strip() or None
    
    if entity_type and field_name:
        # Check if config exists
        config = db.query(DropdownConfig).filter(
            DropdownConfig.entity_type == entity_type,
            DropdownConfig.field_name == field_name
        ).first()
        
        if config:
            config.dropdown_enabled = dropdown_enabled
            config.dropdown_category = dropdown_category
        else:
            config = DropdownConfig(
                entity_type=entity_type,
                field_name=field_name,
                dropdown_enabled=dropdown_enabled,
                dropdown_category=dropdown_category
            )
            db.add(config)
        
        db.commit()
    
    from fastapi.responses import RedirectResponse
    return RedirectResponse(url="/settings", status_code=303)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
