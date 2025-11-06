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

# Create default user if not exists
def create_default_user():
    """Create default user for development/demo purposes"""
    from database import SessionLocal
    db = SessionLocal()
    try:
        existing_user = db.query(User).filter(User.user_id == 1).first()
        if not existing_user:
            default_user = User(
                user_id=1,
                username="admin",
                email="admin@revize-app.cz",
                password_hash="placeholder_hash"
            )
            db.add(default_user)
            db.commit()
            print("✅ Vytvořen výchozí uživatel: admin")
    except Exception as e:
        print(f"⚠️  Chyba při vytváření výchozího uživatele: {e}")
        db.rollback()
    finally:
        db.close()

# Create default user on startup
create_default_user()

# Initialize FastAPI app
app = FastAPI(title="Revize App")

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
    
    return templates.TemplateResponse("switchboard_form.html", {
        "request": request,
        "user_id": user_id,
        "revision": revision,
        "switchboard": None
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
    
    return templates.TemplateResponse("switchboard_form.html", {
        "request": request,
        "user_id": user_id,
        "revision": switchboard.revision,
        "switchboard": switchboard
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
    
    return templates.TemplateResponse("device_form.html", {
        "request": request,
        "user_id": user_id,
        "switchboard": switchboard,
        "device": None,
        "devices": devices
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
    
    return templates.TemplateResponse("device_form.html", {
        "request": request,
        "user_id": user_id,
        "switchboard": device.switchboard,
        "device": device,
        "devices": devices
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
