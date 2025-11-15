import os
from typing import Optional

from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from passlib.hash import bcrypt

from database import engine, Base, get_db
from models import (
    User,
    Revision,
    Switchboard,
    SwitchboardMeasurement,
    SwitchboardDevice,
    Circuit,
    CircuitMeasurement,
    TerminalDevice,
    TerminalMeasurement,
)

app = FastAPI(title="Revizní app – clean v2")

Base.metadata.create_all(bind=engine)

templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY environment variable must be set")
app.add_middleware(SessionMiddleware, secret_key=SECRET_KEY)


def get_current_user_id() -> int:
    return 1


def ensure_default_user(db: Session) -> User:
    user = db.query(User).filter(User.user_id == 1).first()
    if not user:
        user = User(
            user_id=1,
            username="admin",
            email="admin@example.com",
            password_hash=bcrypt.hash(os.getenv("ADMIN_PASSWORD", "admin")),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


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
        .order_by(Revision.revision_date_of_creation.desc().nullslast())
        .all()
    )
    return templates.TemplateResponse(
        "revisions_list.html",
        {"request": request, "revisions": revisions},
    )


@app.get("/revisions/create", response_class=HTMLResponse)
async def revision_create_form(request: Request):
    return templates.TemplateResponse(
        "revision_form.html", {"request": request, "revision": None}
    )


@app.post("/revisions/create")
async def revision_create(
    request: Request,
    revision_name: str = Form(...),
    revision_code: str = Form(""),
    revision_address: str = Form(""),
    revision_short_description: str = Form(""),
    db: Session = Depends(get_db),
):
    user_id = get_current_user_id()
    ensure_default_user(db)
    rev = Revision(
        user_id=user_id,
        revision_name=revision_name,
        revision_code=revision_code or None,
        revision_address=revision_address or None,
        revision_short_description=revision_short_description or None,
    )
    db.add(rev)
    db.commit()
    db.refresh(rev)
    return RedirectResponse(url=f"/revisions/{rev.revision_id}", status_code=303)


@app.get("/revisions/{revision_id}", response_class=HTMLResponse)
async def revision_detail(
    revision_id: int, request: Request, db: Session = Depends(get_db)
):
    user_id = get_current_user_id()
    rev = (
        db.query(Revision)
        .filter(Revision.revision_id == revision_id, Revision.user_id == user_id)
        .first()
    )
    if not rev:
        return RedirectResponse(url="/revisions", status_code=303)

    switchboards = (
        db.query(Switchboard)
        .filter(Switchboard.revision_id == revision_id)
        .order_by(Switchboard.switchboard_order.asc())
        .all()
    )

    return templates.TemplateResponse(
        "revision_detail.html",
        {
            "request": request,
            "revision": rev,
            "switchboards": switchboards,
        },
    )


@app.get("/revisions/{revision_id}/edit", response_class=HTMLResponse)
async def revision_edit_form(
    revision_id: int, request: Request, db: Session = Depends(get_db)
):
    user_id = get_current_user_id()
    rev = (
        db.query(Revision)
        .filter(Revision.revision_id == revision_id, Revision.user_id == user_id)
        .first()
    )
    if not rev:
        return RedirectResponse(url="/revisions", status_code=303)

    return templates.TemplateResponse(
        "revision_form.html",
        {"request": request, "revision": rev},
    )


@app.post("/revisions/{revision_id}/edit")
async def revision_edit(
    revision_id: int,
    request: Request,
    revision_name: str = Form(...),
    revision_code: str = Form(""),
    revision_address: str = Form(""),
    revision_short_description: str = Form(""),
    db: Session = Depends(get_db),
):
    user_id = get_current_user_id()
    rev = (
        db.query(Revision)
        .filter(Revision.revision_id == revision_id, Revision.user_id == user_id)
        .first()
    )
    if not rev:
        return RedirectResponse(url="/revisions", status_code=303)

    rev.revision_name = revision_name
    rev.revision_code = revision_code or None
    rev.revision_address = revision_address or None
    rev.revision_short_description = revision_short_description or None

    db.commit()
    return RedirectResponse(url=f"/revisions/{rev.revision_id}", status_code=303)


@app.post("/revisions/{revision_id}/delete")
async def revision_delete(revision_id: int, db: Session = Depends(get_db)):
    user_id = get_current_user_id()
    rev = (
        db.query(Revision)
        .filter(Revision.revision_id == revision_id, Revision.user_id == user_id)
        .first()
    )
    if rev:
        db.delete(rev)
        db.commit()
    return RedirectResponse(url="/revisions", status_code=303)


@app.post("/revisions/{revision_id}/switchboards/create")
async def switchboard_create(
    revision_id: int,
    switchboard_name: str = Form(...),
    switchboard_location: str = Form(""),
    switchboard_note: str = Form(""),
    db: Session = Depends(get_db),
):
    user_id = get_current_user_id()
    rev = (
        db.query(Revision)
        .filter(Revision.revision_id == revision_id, Revision.user_id == user_id)
        .first()
    )
    if not rev:
        return RedirectResponse(url="/revisions", status_code=303)

    max_order = (
        db.query(Switchboard.switchboard_order)
        .filter(Switchboard.revision_id == revision_id)
        .order_by(Switchboard.switchboard_order.desc())
        .first()
    )
    next_order = (max_order[0] + 1) if max_order else 1

    sb = Switchboard(
        revision_id=revision_id,
        switchboard_name=switchboard_name,
        switchboard_location=switchboard_location or None,
        switchboard_note=switchboard_note or None,
        switchboard_order=next_order,
    )
    db.add(sb)
    db.commit()
    db.refresh(sb)
    return RedirectResponse(url=f"/switchboards/{sb.switchboard_id}", status_code=303)


@app.get("/switchboards/{switchboard_id}", response_class=HTMLResponse)
async def switchboard_detail(
    switchboard_id: int, request: Request, db: Session = Depends(get_db)
):
    user_id = get_current_user_id()
    sb = (
        db.query(Switchboard)
        .join(Revision)
        .filter(
            Switchboard.switchboard_id == switchboard_id,
            Revision.user_id == user_id,
        )
        .first()
    )
    if not sb:
        return RedirectResponse(url="/revisions", status_code=303)

    meas = (
        db.query(SwitchboardMeasurement)
        .filter(SwitchboardMeasurement.switchboard_id == switchboard_id)
        .first()
    )

    devices = (
        db.query(SwitchboardDevice)
        .filter(SwitchboardDevice.switchboard_id == switchboard_id)
        .order_by(SwitchboardDevice.switchboard_device_position.asc().nullslast())
        .all()
    )

    circuits = (
        db.query(Circuit)
        .join(SwitchboardDevice, Circuit.device_id == SwitchboardDevice.device_id)
        .filter(SwitchboardDevice.switchboard_id == switchboard_id)
        .order_by(Circuit.circuit_number.asc().nullslast())
        .all()
    )

    return templates.TemplateResponse(
        "switchboard_detail.html",
        {
            "request": request,
            "switchboard": sb,
            "measurement": meas,
            "devices": devices,
            "circuits": circuits,
            "revision": sb.revision,
        },
    )


@app.post("/switchboards/{switchboard_id}/edit")
async def switchboard_edit(
    switchboard_id: int,
    switchboard_name: str = Form(...),
    switchboard_location: str = Form(""),
    switchboard_note: str = Form(""),
    db: Session = Depends(get_db),
):
    user_id = get_current_user_id()
    sb = (
        db.query(Switchboard)
        .join(Revision)
        .filter(
            Switchboard.switchboard_id == switchboard_id,
            Revision.user_id == user_id,
        )
        .first()
    )
    if not sb:
        return RedirectResponse(url="/revisions", status_code=303)

    sb.switchboard_name = switchboard_name
    sb.switchboard_location = switchboard_location or None
    sb.switchboard_note = switchboard_note or None

    db.commit()
    return RedirectResponse(url=f"/switchboards/{sb.switchboard_id}", status_code=303)


@app.post("/switchboards/{switchboard_id}/delete")
async def switchboard_delete(switchboard_id: int, db: Session = Depends(get_db)):
    user_id = get_current_user_id()
    sb = (
        db.query(Switchboard)
        .join(Revision)
        .filter(
            Switchboard.switchboard_id == switchboard_id,
            Revision.user_id == user_id,
        )
        .first()
    )
    if sb:
        rev_id = sb.revision_id
        db.delete(sb)
        db.commit()
        return RedirectResponse(url=f"/revisions/{rev_id}", status_code=303)
    return RedirectResponse(url="/revisions", status_code=303)


@app.post("/switchboards/{switchboard_id}/measurements/save")
async def switchboard_measurements_save(
    switchboard_id: int,
    measurements_switchboard_insulation_resistance: Optional[float] = Form(None),
    measurements_switchboard_loop_impedance_min: Optional[float] = Form(None),
    measurements_switchboard_loop_impedance_max: Optional[float] = Form(None),
    measurements_switchboard_rcd_trip_time_ms: Optional[float] = Form(None),
    measurements_switchboard_rcd_test_current_ma: Optional[float] = Form(None),
    measurements_switchboard_earth_resistance: Optional[float] = Form(None),
    db: Session = Depends(get_db),
):
    user_id = get_current_user_id()
    sb = (
        db.query(Switchboard)
        .join(Revision)
        .filter(
            Switchboard.switchboard_id == switchboard_id,
            Revision.user_id == user_id,
        )
        .first()
    )
    if not sb:
        return RedirectResponse(url="/revisions", status_code=303)

    meas = (
        db.query(SwitchboardMeasurement)
        .filter(SwitchboardMeasurement.switchboard_id == switchboard_id)
        .first()
    )
    if not meas:
        meas = SwitchboardMeasurement(switchboard_id=switchboard_id)
        db.add(meas)

    meas.measurements_switchboard_insulation_resistance = (
        measurements_switchboard_insulation_resistance
    )
    meas.measurements_switchboard_loop_impedance_min = (
        measurements_switchboard_loop_impedance_min
    )
    meas.measurements_switchboard_loop_impedance_max = (
        measurements_switchboard_loop_impedance_max
    )
    meas.measurements_switchboard_rcd_trip_time_ms = (
        measurements_switchboard_rcd_trip_time_ms
    )
    meas.measurements_switchboard_rcd_test_current_ma = (
        measurements_switchboard_rcd_test_current_ma
    )
    meas.measurements_switchboard_earth_resistance = (
        measurements_switchboard_earth_resistance
    )

    db.commit()
    return RedirectResponse(url=f"/switchboards/{switchboard_id}", status_code=303)


@app.post("/switchboards/{switchboard_id}/devices/create")
async def device_create(
    switchboard_id: int,
    switchboard_device_position: str = Form(""),
    switchboard_device_type: str = Form(""),
    switchboard_device_manufacturer: str = Form(""),
    switchboard_device_model: str = Form(""),
    switchboard_device_trip_characteristic: str = Form(""),
    switchboard_device_rated_current: Optional[float] = Form(None),
    switchboard_device_residual_current_ma: Optional[float] = Form(None),
    switchboard_device_poles: Optional[int] = Form(None),
    switchboard_device_module_width: Optional[float] = Form(None),
    db: Session = Depends(get_db),
):
    user_id = get_current_user_id()
    sb = (
        db.query(Switchboard)
        .join(Revision)
        .filter(
            Switchboard.switchboard_id == switchboard_id,
            Revision.user_id == user_id,
        )
        .first()
    )
    if not sb:
        return RedirectResponse(url="/revisions", status_code=303)

    dev = SwitchboardDevice(
        switchboard_id=switchboard_id,
        switchboard_device_position=switchboard_device_position or None,
        switchboard_device_type=switchboard_device_type or None,
        switchboard_device_manufacturer=switchboard_device_manufacturer or None,
        switchboard_device_model=switchboard_device_model or None,
        switchboard_device_trip_characteristic=switchboard_device_trip_characteristic
        or None,
        switchboard_device_rated_current=switchboard_device_rated_current,
        switchboard_device_residual_current_ma=switchboard_device_residual_current_ma,
        switchboard_device_poles=switchboard_device_poles,
        switchboard_device_module_width=switchboard_device_module_width,
    )
    db.add(dev)
    db.commit()
    return RedirectResponse(url=f"/switchboards/{switchboard_id}", status_code=303)


@app.post("/devices/{device_id}/delete")
async def device_delete(device_id: int, db: Session = Depends(get_db)):
    user_id = get_current_user_id()
    dev = (
        db.query(SwitchboardDevice)
        .join(Switchboard)
        .join(Revision)
        .filter(
            SwitchboardDevice.device_id == device_id,
            Revision.user_id == user_id,
        )
        .first()
    )
    if dev:
        sb_id = dev.switchboard_id
        db.delete(dev)
        db.commit()
        return RedirectResponse(url=f"/switchboards/{sb_id}", status_code=303)
    return RedirectResponse(url="/revisions", status_code=303)


@app.post("/devices/{device_id}/circuits/create")
async def circuit_create(
    device_id: int,
    circuit_number: str = Form(""),
    circuit_room: str = Form(""),
    circuit_description: str = Form(""),
    circuit_number_of_outlets: Optional[int] = Form(None),
    circuit_cable: str = Form(""),
    db: Session = Depends(get_db),
):
    user_id = get_current_user_id()
    dev = (
        db.query(SwitchboardDevice)
        .join(Switchboard)
        .join(Revision)
        .filter(
            SwitchboardDevice.device_id == device_id,
            Revision.user_id == user_id,
        )
        .first()
    )
    if not dev:
        return RedirectResponse(url="/revisions", status_code=303)

    circ = Circuit(
        device_id=device_id,
        circuit_number=circuit_number or None,
        circuit_room=circuit_room or None,
        circuit_description=circuit_description or None,
        circuit_number_of_outlets=circuit_number_of_outlets,
        circuit_cable=circuit_cable or None,
    )
    db.add(circ)
    db.commit()
    return RedirectResponse(
        url=f"/switchboards/{dev.switchboard_id}", status_code=303
    )


@app.post("/circuits/{circuit_id}/delete")
async def circuit_delete(circuit_id: int, db: Session = Depends(get_db)):
    user_id = get_current_user_id()
    circ = (
        db.query(Circuit)
        .join(SwitchboardDevice)
        .join(Switchboard)
        .join(Revision)
        .filter(
            Circuit.circuit_id == circuit_id,
            Revision.user_id == user_id,
        )
        .first()
    )
    if circ:
        sb_id = circ.device.switchboard_id
        db.delete(circ)
        db.commit()
        return RedirectResponse(url=f"/switchboards/{sb_id}", status_code=303)
    return RedirectResponse(url="/revisions", status_code=303)


@app.post("/circuits/{circuit_id}/measurements/save")
async def circuit_measurements_save(
    circuit_id: int,
    measurements_circuit_insulation_resistance: Optional[float] = Form(None),
    measurements_circuit_loop_impedance_min: Optional[float] = Form(None),
    measurements_circuit_loop_impedance_max: Optional[float] = Form(None),
    measurements_circuit_rcd_trip_time_ms: Optional[float] = Form(None),
    measurements_circuit_rcd_test_current_ma: Optional[float] = Form(None),
    measurements_circuit_earth_resistance: Optional[float] = Form(None),
    measurements_circuit_continuity: Optional[float] = Form(None),
    measurements_circuit_order_of_phases: str = Form(""),
    db: Session = Depends(get_db),
):
    user_id = get_current_user_id()
    circ = (
        db.query(Circuit)
        .join(SwitchboardDevice)
        .join(Switchboard)
        .join(Revision)
        .filter(
            Circuit.circuit_id == circuit_id,
            Revision.user_id == user_id,
        )
        .first()
    )
    if not circ:
        return RedirectResponse(url="/revisions", status_code=303)

    meas = (
        db.query(CircuitMeasurement)
        .filter(CircuitMeasurement.circuit_id == circuit_id)
        .first()
    )
    if not meas:
        meas = CircuitMeasurement(circuit_id=circuit_id)
        db.add(meas)

    meas.measurements_circuit_insulation_resistance = (
        measurements_circuit_insulation_resistance
    )
    meas.measurements_circuit_loop_impedance_min = (
        measurements_circuit_loop_impedance_min
    )
    meas.measurements_circuit_loop_impedance_max = (
        measurements_circuit_loop_impedance_max
    )
    meas.measurements_circuit_rcd_trip_time_ms = (
        measurements_circuit_rcd_trip_time_ms
    )
    meas.measurements_circuit_rcd_test_current_ma = (
        measurements_circuit_rcd_test_current_ma
    )
    meas.measurements_circuit_earth_resistance = (
        measurements_circuit_earth_resistance
    )
    meas.measurements_circuit_continuity = measurements_circuit_continuity
    meas.measurements_circuit_order_of_phases = (
        measurements_circuit_order_of_phases or None
    )

    db.commit()
    return RedirectResponse(
        url=f"/switchboards/{circ.device.switchboard_id}", status_code=303
    )

def recompute_circuit_measurement(db: Session, circuit_id: int) -> None:
    """Agregace měření z koncových zařízení do měření obvodu.

    Vezme všechna TerminalMeasurement u daného obvodu a spočítá:
    - Zs min / max
    - max. vypínací čas RCD
    - max. zkušební proud RCD
    a tyto hodnoty uloží do CircuitMeasurement.
    """
    tms = (
        db.query(TerminalMeasurement)
        .join(TerminalDevice)
        .filter(TerminalDevice.circuit_id == circuit_id)
        .all()
    )

    if not tms:
        return

    def collect(attr: str):
        vals = [getattr(m, attr) for m in tms if getattr(m, attr) is not None]
        return vals or None

    zs_min_vals = collect("measurements_circuit_loop_impedance_min")
    zs_max_vals = collect("measurements_circuit_loop_impedance_max")
    t_vals = collect("measurements_circuit_rcd_trip_time_ms")
    ir_vals = collect("measurements_circuit_rcd_test_current_ma")
    riso_vals = collect("measurements_circuit_insulation_resistance")

    meas = (
        db.query(CircuitMeasurement)
        .filter(CircuitMeasurement.circuit_id == circuit_id)
        .first()
    )
    if not meas:
        meas = CircuitMeasurement(circuit_id=circuit_id)
        db.add(meas)

    if zs_min_vals:
        meas.measurements_circuit_loop_impedance_min = min(zs_min_vals)
    if zs_max_vals:
        meas.measurements_circuit_loop_impedance_max = max(zs_max_vals)
    if t_vals:
        meas.measurements_circuit_rcd_trip_time_ms = max(t_vals)
    if ir_vals:
        meas.measurements_circuit_rcd_test_current_ma = max(ir_vals)
    if riso_vals:
        meas.measurements_circuit_insulation_resistance = min(riso_vals)

    db.commit()





@app.post("/circuits/{circuit_id}/terminal-devices/create")
async def terminal_device_create(
    circuit_id: int,
    terminal_device_type: str = Form(""),
    terminal_device_manufacturer: str = Form(""),
    terminal_device_model: str = Form(""),
    terminal_device_marking: str = Form(""),
    terminal_device_power: Optional[float] = Form(None),
    terminal_device_ip_rating: str = Form(""),
    terminal_device_protection_class: str = Form(""),
    terminal_device_serial_number: str = Form(""),
    terminal_device_supply_type: str = Form(""),
    terminal_device_installation_method: str = Form(""),
    db: Session = Depends(get_db),
):
    user_id = get_current_user_id()
    circ = (
        db.query(Circuit)
        .join(SwitchboardDevice)
        .join(Switchboard)
        .join(Revision)
        .filter(
            Circuit.circuit_id == circuit_id,
            Revision.user_id == user_id,
        )
        .first()
    )
    if not circ:
        return RedirectResponse(url="/revisions", status_code=303)

    td = TerminalDevice(
        circuit_id=circuit_id,
        terminal_device_type=terminal_device_type or None,
        terminal_device_manufacturer=terminal_device_manufacturer or None,
        terminal_device_model=terminal_device_model or None,
        terminal_device_marking=terminal_device_marking or None,
        terminal_device_power=terminal_device_power,
        terminal_device_ip_rating=terminal_device_ip_rating or None,
        terminal_device_protection_class=terminal_device_protection_class or None,
        terminal_device_serial_number=terminal_device_serial_number or None,
        terminal_device_supply_type=terminal_device_supply_type or None,
        terminal_device_installation_method=terminal_device_installation_method or None,
    )
    db.add(td)
    db.commit()
    return RedirectResponse(
        url=f"/switchboards/{circ.device.switchboard_id}", status_code=303
    )


@app.post("/terminal-devices/{terminal_device_id}/delete")
async def terminal_device_delete(
    terminal_device_id: int, db: Session = Depends(get_db)
):
    user_id = get_current_user_id()
    td = (
        db.query(TerminalDevice)
        .join(Circuit)
        .join(SwitchboardDevice)
        .join(Switchboard)
        .join(Revision)
        .filter(
            TerminalDevice.terminal_device_id == terminal_device_id,
            Revision.user_id == user_id,
        )
        .first()
    )
    if td:
        sb_id = td.circuit.device.switchboard_id
        db.delete(td)
        db.commit()
        return RedirectResponse(url=f"/switchboards/{sb_id}", status_code=303)
    return RedirectResponse(url="/revisions", status_code=303)

@app.post("/terminal-devices/{terminal_device_id}/measurements/save")
async def terminal_device_measurements_save(
    terminal_device_id: int,
    measurements_circuit_insulation_resistance: Optional[float] = Form(None),
    measurements_circuit_loop_impedance_min: Optional[float] = Form(None),
    measurements_circuit_loop_impedance_max: Optional[float] = Form(None),
    measurements_circuit_rcd_trip_time_ms: Optional[float] = Form(None),
    measurements_circuit_rcd_test_current_ma: Optional[float] = Form(None),
    db: Session = Depends(get_db),
):
    """Uložení měření pro konkrétní koncové zařízení a přepočet měření obvodu."""
    user_id = get_current_user_id()
    td = (
        db.query(TerminalDevice)
        .join(Circuit)
        .join(SwitchboardDevice)
        .join(Switchboard)
        .join(Revision)
        .filter(
            TerminalDevice.terminal_device_id == terminal_device_id,
            Revision.user_id == user_id,
        )
        .first()
    )
    if not td:
        return RedirectResponse(url="/revisions", status_code=303)

    meas = (
        db.query(TerminalMeasurement)
        .filter(TerminalMeasurement.terminal_device_id == terminal_device_id)
        .first()
    )
    if not meas:
        meas = TerminalMeasurement(terminal_device_id=terminal_device_id)
        db.add(meas)

    meas.measurements_circuit_insulation_resistance = (
        measurements_circuit_insulation_resistance
    )
    meas.measurements_circuit_loop_impedance_min = (
        measurements_circuit_loop_impedance_min
    )
    meas.measurements_circuit_loop_impedance_max = (
        measurements_circuit_loop_impedance_max
    )
    meas.measurements_circuit_rcd_trip_time_ms = (
        measurements_circuit_rcd_trip_time_ms
    )
    meas.measurements_circuit_rcd_test_current_ma = (
        measurements_circuit_rcd_test_current_ma
    )

    db.commit()

    # následně přepočítáme agregované hodnoty obvodu
    recompute_circuit_measurement(db, td.circuit_id)

    return RedirectResponse(url=f"/circuits/{td.circuit_id}", status_code=303)





@app.get("/circuits/{circuit_id}", response_class=HTMLResponse)
async def circuit_detail(circuit_id: int, request: Request, db: Session = Depends(get_db)):
    """
    Detail obvodu – základní údaje, měření a koncová zařízení.
    """
    user_id = get_current_user_id()
    circ = (
        db.query(Circuit)
        .join(SwitchboardDevice)
        .join(Switchboard)
        .join(Revision)
        .filter(
            Circuit.circuit_id == circuit_id,
            Revision.user_id == user_id,
        )
        .first()
    )
    if not circ:
        return RedirectResponse(url="/revisions", status_code=303)

    # nacteme merici radek, pokud existuje
    meas = (
        db.query(CircuitMeasurement)
        .filter(CircuitMeasurement.circuit_id == circuit_id)
        .first()
    )

    return templates.TemplateResponse(
        "circuit_detail.html",
        {
            "request": request,
            "circuit": circ,
            "measurement": meas,
            "switchboard": circ.device.switchboard,
            "revision": circ.device.switchboard.revision,
        },
    )


@app.post("/circuits/{circuit_id}/edit")
async def circuit_edit(
    circuit_id: int,
    circuit_number: str = Form(""),
    circuit_room: str = Form(""),
    circuit_description: str = Form(""),
    circuit_number_of_outlets: Optional[int] = Form(None),
    circuit_cable: str = Form(""),
    circuit_cable_termination: str = Form(""),
    circuit_cable_installation_method: str = Form(""),
    db: Session = Depends(get_db),
):
    """
    Ulozeni zakladnich udaju obvodu.
    """
    user_id = get_current_user_id()
    circ = (
        db.query(Circuit)
        .join(SwitchboardDevice)
        .join(Switchboard)
        .join(Revision)
        .filter(
            Circuit.circuit_id == circuit_id,
            Revision.user_id == user_id,
        )
        .first()
    )
    if not circ:
        return RedirectResponse(url="/revisions", status_code=303)

    circ.circuit_number = circuit_number or None
    circ.circuit_room = circuit_room or None
    circ.circuit_description = circuit_description or None
    circ.circuit_number_of_outlets = circuit_number_of_outlets
    circ.circuit_cable = circuit_cable or None
    circ.circuit_cable_termination = circuit_cable_termination or None
    circ.circuit_cable_installation_method = circuit_cable_installation_method or None

    db.commit()
    return RedirectResponse(url=f"/circuits/{circ.circuit_id}", status_code=303)

