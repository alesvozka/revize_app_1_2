import os
from typing import Optional

from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from passlib.hash import bcrypt

from database import Base, engine, get_db
from models import User, Revision, Switchboard, Device, Circuit


app = FastAPI(title="Revizní app – zjednodušená verze")

# Create tables
Base.metadata.create_all(bind=engine)

# Templates & static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")


# --- helpers ---


def get_current_user_id() -> int:
    """For now we run in single-user mode: always user 1.

    On first call we ensure default admin user exists.
    """
    return 1


def ensure_default_user(db: Session) -> User:
    user = db.query(User).filter(User.id == 1).first()
    if not user:
        user = User(
            id=1,
            username="admin",
            email="admin@example.com",
            password_hash=bcrypt.hash(os.getenv("ADMIN_PASSWORD", "admin")),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


# --- routes ---


@app.get("/", response_class=HTMLResponse)
async def index(request: Request, db: Session = Depends(get_db)):
    ensure_default_user(db)
    return RedirectResponse(url="/revisions", status_code=303)


@app.get("/revisions", response_class=HTMLResponse)
async def revisions_list(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user_id()
    ensure_default_user(db)
    revisions = (
        db.query(Revision)
        .filter(Revision.user_id == user_id)
        .order_by(Revision.created_at.desc())
        .all()
    )
    return templates.TemplateResponse(
        "revisions_list.html",
        {"request": request, "revisions": revisions},
    )


@app.get("/revisions/create", response_class=HTMLResponse)
async def revision_create_form(request: Request):
    return templates.TemplateResponse("revision_form.html", {"request": request, "revision": None})


@app.post("/revisions/create")
async def revision_create(
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    location: str = Form(""),
    db: Session = Depends(get_db),
):
    user_id = get_current_user_id()
    ensure_default_user(db)
    revision = Revision(
        user_id=user_id,
        title=title,
        description=description,
        location=location,
    )
    db.add(revision)
    db.commit()
    db.refresh(revision)
    return RedirectResponse(url=f"/revisions/{revision.id}", status_code=303)


@app.get("/revisions/{revision_id}", response_class=HTMLResponse)
async def revision_detail(revision_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user_id()
    revision = (
        db.query(Revision)
        .filter(Revision.id == revision_id, Revision.user_id == user_id)
        .first()
    )
    if not revision:
        return RedirectResponse(url="/revisions", status_code=303)

    return templates.TemplateResponse(
        "revision_detail.html",
        {
            "request": request,
            "revision": revision,
        },
    )


@app.get("/revisions/{revision_id}/edit", response_class=HTMLResponse)
async def revision_edit_form(revision_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user_id()
    revision = (
        db.query(Revision)
        .filter(Revision.id == revision_id, Revision.user_id == user_id)
        .first()
    )
    if not revision:
        return RedirectResponse(url="/revisions", status_code=303)

    return templates.TemplateResponse(
        "revision_form.html",
        {
            "request": request,
            "revision": revision,
        },
    )


@app.post("/revisions/{revision_id}/edit")
async def revision_edit(
    revision_id: int,
    request: Request,
    title: str = Form(...),
    description: str = Form(""),
    location: str = Form(""),
    db: Session = Depends(get_db),
):
    user_id = get_current_user_id()
    revision = (
        db.query(Revision)
        .filter(Revision.id == revision_id, Revision.user_id == user_id)
        .first()
    )
    if not revision:
        return RedirectResponse(url="/revisions", status_code=303)

    revision.title = title
    revision.description = description
    revision.location = location
    db.commit()
    return RedirectResponse(url=f"/revisions/{revision.id}", status_code=303)


@app.post("/revisions/{revision_id}/delete")
async def revision_delete(revision_id: int, db: Session = Depends(get_db)):
    user_id = get_current_user_id()
    revision = (
        db.query(Revision)
        .filter(Revision.id == revision_id, Revision.user_id == user_id)
        .first()
    )
    if revision:
        db.delete(revision)
        db.commit()
    return RedirectResponse(url="/revisions", status_code=303)


# --- switchboards ---


@app.post("/revisions/{revision_id}/switchboards/create")
async def switchboard_create(
    revision_id: int,
    name: str = Form(...),
    code: str = Form(""),
    location: str = Form(""),
    note: str = Form(""),
    db: Session = Depends(get_db),
):
    user_id = get_current_user_id()
    revision = (
        db.query(Revision)
        .filter(Revision.id == revision_id, Revision.user_id == user_id)
        .first()
    )
    if not revision:
        return RedirectResponse(url="/revisions", status_code=303)

    # determine next order
    max_order = (
        db.query(Switchboard.display_order)
        .filter(Switchboard.revision_id == revision_id)
        .order_by(Switchboard.display_order.desc())
        .first()
    )
    next_order = (max_order[0] + 1) if max_order else 1

    sb = Switchboard(
        revision_id=revision_id,
        name=name,
        code=code,
        location=location,
        note=note,
        display_order=next_order,
    )
    db.add(sb)
    db.commit()
    db.refresh(sb)
    return RedirectResponse(url=f"/switchboards/{sb.id}", status_code=303)


@app.get("/switchboards/{switchboard_id}", response_class=HTMLResponse)
async def switchboard_detail(switchboard_id: int, request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user_id()
    sb = (
        db.query(Switchboard)
        .join(Revision)
        .filter(Switchboard.id == switchboard_id, Revision.user_id == user_id)
        .first()
    )
    if not sb:
        return RedirectResponse(url="/revisions", status_code=303)

    return templates.TemplateResponse(
        "switchboard_detail.html",
        {
            "request": request,
            "switchboard": sb,
            "revision": sb.revision,
        },
    )


@app.post("/switchboards/{switchboard_id}/edit")
async def switchboard_edit(
    switchboard_id: int,
    name: str = Form(...),
    code: str = Form(""),
    location: str = Form(""),
    note: str = Form(""),
    db: Session = Depends(get_db),
):
    user_id = get_current_user_id()
    sb = (
        db.query(Switchboard)
        .join(Revision)
        .filter(Switchboard.id == switchboard_id, Revision.user_id == user_id)
        .first()
    )
    if not sb:
        return RedirectResponse(url="/revisions", status_code=303)

    sb.name = name
    sb.code = code
    sb.location = location
    sb.note = note
    db.commit()
    return RedirectResponse(url=f"/switchboards/{sb.id}", status_code=303)


@app.post("/switchboards/{switchboard_id}/delete")
async def switchboard_delete(switchboard_id: int, db: Session = Depends(get_db)):
    user_id = get_current_user_id()
    sb = (
        db.query(Switchboard)
        .join(Revision)
        .filter(Switchboard.id == switchboard_id, Revision.user_id == user_id)
        .first()
    )
    if sb:
        revision_id = sb.revision_id
        db.delete(sb)
        db.commit()
        return RedirectResponse(url=f"/revisions/{revision_id}", status_code=303)
    return RedirectResponse(url="/revisions", status_code=303)


# --- devices ---


@app.post("/switchboards/{switchboard_id}/devices/create")
async def device_create(
    switchboard_id: int,
    label: str = Form(""),
    description: str = Form(""),
    breaker_type: str = Form("MCB"),
    characteristic: str = Form("B"),
    rated_current: float = Form(16),
    poles: int = Form(1),
    rcd_sensitivity: Optional[float] = Form(None),
    note: str = Form(""),
    db: Session = Depends(get_db),
):
    user_id = get_current_user_id()
    sb = (
        db.query(Switchboard)
        .join(Revision)
        .filter(Switchboard.id == switchboard_id, Revision.user_id == user_id)
        .first()
    )
    if not sb:
        return RedirectResponse(url="/revisions", status_code=303)

    max_row = (
        db.query(Device.row_order)
        .filter(Device.switchboard_id == switchboard_id)
        .order_by(Device.row_order.desc())
        .first()
    )
    next_row = (max_row[0] + 1) if max_row else 1

    dev = Device(
        switchboard_id=switchboard_id,
        row_order=next_row,
        label=label,
        description=description,
        breaker_type=breaker_type,
        characteristic=characteristic,
        rated_current=rated_current,
        poles=poles,
        rcd_sensitivity=rcd_sensitivity,
        note=note,
    )
    db.add(dev)
    db.commit()
    db.refresh(dev)
    return RedirectResponse(url=f"/switchboards/{switchboard_id}", status_code=303)


@app.post("/devices/{device_id}/edit")
async def device_edit(
    device_id: int,
    label: str = Form(""),
    description: str = Form(""),
    breaker_type: str = Form("MCB"),
    characteristic: str = Form("B"),
    rated_current: float = Form(16),
    poles: int = Form(1),
    rcd_sensitivity: Optional[float] = Form(None),
    note: str = Form(""),
    db: Session = Depends(get_db),
):
    user_id = get_current_user_id()
    dev = (
        db.query(Device)
        .join(Switchboard).join(Revision)
        .filter(Device.id == device_id, Revision.user_id == user_id)
        .first()
    )
    if not dev:
        return RedirectResponse(url="/revisions", status_code=303)

    dev.label = label
    dev.description = description
    dev.breaker_type = breaker_type
    dev.characteristic = characteristic
    dev.rated_current = rated_current
    dev.poles = poles
    dev.rcd_sensitivity = rcd_sensitivity
    dev.note = note
    db.commit()
    return RedirectResponse(url=f"/switchboards/{dev.switchboard_id}", status_code=303)


@app.post("/devices/{device_id}/delete")
async def device_delete(device_id: int, db: Session = Depends(get_db)):
    user_id = get_current_user_id()
    dev = (
        db.query(Device)
        .join(Switchboard).join(Revision)
        .filter(Device.id == device_id, Revision.user_id == user_id)
        .first()
    )
    if dev:
        switchboard_id = dev.switchboard_id
        db.delete(dev)
        db.commit()
        return RedirectResponse(url=f"/switchboards/{switchboard_id}", status_code=303)
    return RedirectResponse(url="/revisions", status_code=303)


# --- circuits ---


@app.post("/devices/{device_id}/circuits/create")
async def circuit_create(
    device_id: int,
    room: str = Form(""),
    usage: str = Form(""),
    cable_type: str = Form(""),
    cable_size: str = Form(""),
    length: float = Form(0),
    outlets_count: int = Form(0),
    note: str = Form(""),
    db: Session = Depends(get_db),
):
    user_id = get_current_user_id()
    dev = (
        db.query(Device)
        .join(Switchboard).join(Revision)
        .filter(Device.id == device_id, Revision.user_id == user_id)
        .first()
    )
    if not dev:
        return RedirectResponse(url="/revisions", status_code=303)

    circ = Circuit(
        device_id=device_id,
        room=room,
        usage=usage,
        cable_type=cable_type,
        cable_size=cable_size,
        length=length,
        outlets_count=outlets_count,
        note=note,
    )
    db.add(circ)
    db.commit()
    return RedirectResponse(url=f"/switchboards/{dev.switchboard_id}", status_code=303)


@app.post("/circuits/{circuit_id}/edit")
async def circuit_edit(
    circuit_id: int,
    room: str = Form(""),
    usage: str = Form(""),
    cable_type: str = Form(""),
    cable_size: str = Form(""),
    length: float = Form(0),
    outlets_count: int = Form(0),
    note: str = Form(""),
    db: Session = Depends(get_db),
):
    user_id = get_current_user_id()
    circ = (
        db.query(Circuit)
        .join(Device).join(Switchboard).join(Revision)
        .filter(Circuit.id == circuit_id, Revision.user_id == user_id)
        .first()
    )
    if not circ:
        return RedirectResponse(url="/revisions", status_code=303)

    circ.room = room
    circ.usage = usage
    circ.cable_type = cable_type
    circ.cable_size = cable_size
    circ.length = length
    circ.outlets_count = outlets_count
    circ.note = note
    db.commit()
    return RedirectResponse(url=f"/switchboards/{circ.device.switchboard_id}", status_code=303)


@app.post("/circuits/{circuit_id}/delete")
async def circuit_delete(circuit_id: int, db: Session = Depends(get_db)):
    user_id = get_current_user_id()
    circ = (
        db.query(Circuit)
        .join(Device).join(Switchboard).join(Revision)
        .filter(Circuit.id == circuit_id, Revision.user_id == user_id)
        .first()
    )
    if circ:
        switchboard_id = circ.device.switchboard_id
        db.delete(circ)
        db.commit()
        return RedirectResponse(url=f"/switchboards/{switchboard_id}", status_code=303)
    return RedirectResponse(url="/revisions", status_code=303)
