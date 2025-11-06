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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
