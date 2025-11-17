import os
from typing import Optional

from fastapi import FastAPI, Request, Depends, Form
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import text
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


def auto_migrate():
    """Simple idempotent migrations for new columns."""
    from database import SessionLocal
    db = SessionLocal()
    try:
        # Add cable columns to terminal_devices if they do not exist
        db.execute(text(
            "ALTER TABLE terminal_devices "
            "ADD COLUMN IF NOT EXISTS terminal_device_cable VARCHAR(255);"
        ))
        db.execute(text(
            "ALTER TABLE terminal_devices "
            "ADD COLUMN IF NOT EXISTS terminal_device_cable_installation_method VARCHAR(255);"
        ))
        # Add quantity column to terminal_devices if it does not exist
        db.execute(text(
            "ALTER TABLE terminal_devices "
            "ADD COLUMN IF NOT EXISTS terminal_device_quantity INTEGER;"
        ))
        db.commit()
        print("Auto-migration completed.")
    except Exception as e:
        db.rollback()
        print("Auto-migration error:", e)
    finally:
        db.close()


auto_migrate()



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
            username="demo",
            email="demo@example.com",
            password_hash=bcrypt.hash("demo"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    return user


@app.middleware("http")
async def add_default_user(request: Request, call_next):
    db = next(get_db())
    ensure_default_user(db)
    db.close()
    response = await call_next(request)
    return response


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return RedirectResponse(url="/revisions", status_code=303)


@app.get("/revisions", response_class=HTMLResponse)
async def revisions_list(request: Request, db: Session = Depends(get_db)):
    user_id = get_current_user_id()
    revisions = (
        db.query(Revision)
        .filter(Revision.user_id == user_id)
        .order_by(Revision.revision_created_at.desc())
        .all()
    )
    return templates.TemplateResponse(
        "revisions_list.html",
        {
            "request": request,
            "revisions": revisions,
        },
    )


@app.get("/revisions/create", response_class=HTMLResponse)
async def revision_create_form(request: Request):
    return templates.TemplateResponse(
        "revision_form.html",
        {"request": request, "revision": None},
    )


@app.post("/revisions/create")
async def revision_create(
    request: Request,
    revision_name: str = Form(...),
    client_name: str = Form(""),
    client_address: str = Form(""),
    client_ic: str = Form(""),
    client_dic: str = Form(""),
    building_name: str = Form(""),
    building_address: str = Form(""),
    building_parcel_number: str = Form(""),
    building_description: str = Form(""),
    db: Session = Depends(get_db),
):
    user_id = get_current_user_id()
    rev = Revision(
        user_id=user_id,
        revision_name=revision_name,
        client_name=client_name or None,
        client_address=client_address or None,
        client_ic=client_ic or None,
        client_dic=client_dic or None,
        building_name=building_name or None,
        building_address=building_address or None,
        building_parcel_number=building_parcel_number or None,
        building_description=building_description or None,
    )
    db.add(rev)
    db.commit()
    db.refresh(rev)

    sb = Switchboard(
        revision_id=rev.revision_id,
        switchboard_name="Rozvaděč 1",
        switchboard_location=None,
        switchboard_description=None,
        switchboard_order=1,
    )
    db.add(sb)
    db.commit()
    db.refresh(sb)

    meas = SwitchboardMeasurement(
        switchboard_id=sb.switchboard_id,
    )
    db.add(meas)
    db.commit()

    return RedirectResponse(
        url=f"/revisions/{rev.revision_id}", status_code=303
    )


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
    revision_name: str = Form(...),
    client_name: str = Form(""),
    client_address: str = Form(""),
    client_ic: str = Form(""),
    client_dic: str = Form(""),
    building_name: str = Form(""),
    building_address: str = Form(""),
    building_parcel_number: str = Form(""),
    building_description: str = Form(""),
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
    rev.client_name = client_name or None
    rev.client_address = client_address or None
    rev.client_ic = client_ic or None
    rev.client_dic = client_dic or None
    rev.building_name = building_name or None
    rev.building_address = building_address or None
    rev.building_parcel_number = building_parcel_number or None
    rev.building_description = building_description or None

    db.commit()
    return RedirectResponse(url=f"/revisions/{revision_id}", status_code=303)


@app.post("/revisions/{revision_id}/delete")
async def revision_delete(
    revision_id: int, request: Request, db: Session = Depends(get_db)
):
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
    switchboard_name: str = Form(""),
    switchboard_location: str = Form(""),
    switchboard_description: str = Form(""),
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
        switchboard_name=switchboard_name or None,
        switchboard_location=switchboard_location or None,
        switchboard_description=switchboard_description or None,
        switchboard_order=next_order,
    )
    db.add(sb)
    db.commit()
    db.refresh(sb)

    meas = SwitchboardMeasurement(switchboard_id=sb.switchboard_id)
    db.add(meas)
    db.commit()

    return RedirectResponse(
        url=f"/revisions/{revision_id}", status_code=303
    )


@app.post("/switchboards/{switchboard_id}/delete")
async def switchboard_delete(
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
    if sb:
        revision_id = sb.revision_id
        db.delete(sb)
        db.commit()
        return RedirectResponse(
            url=f"/revisions/{revision_id}", status_code=303
        )
    return RedirectResponse(url="/revisions", status_code=303)


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


@app.post("/switchboards/{switchboard_id}/measurements/save")
async def switchboard_measurements_save(
    switchboard_id: int,
    measurements_switchboard_ip_system: str = Form(""),
    measurements_switchboard_type_of_earthing: str = Form(""),
    measurements_switchboard_supply_sources: str = Form(""),
    measurements_switchboard_main_breaker: str = Form(""),
    measurements_switchboard_short_circuit_power: str = Form(""),
    measurements_switchboard_protection_against_electric_shock: str = Form(""),
    measurements_switchboard_external_influences: str = Form(""),
    measurements_switchboard_protection_against_overcurrent: str = Form(""),
    measurements_switchboard_protection_against_overvoltage: str = Form(""),
    measurements_switchboard_overvoltage_category: str = Form(""),
    measurements_switchboard_insulation_resistance: Optional[float] = Form(None),
    measurements_switchboard_loop_impedance: Optional[float] = Form(None),
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

    meas.measurements_switchboard_ip_system = (
        measurements_switchboard_ip_system or None
    )
    meas.measurements_switchboard_type_of_earthing = (
        measurements_switchboard_type_of_earthing or None
    )
    meas.measurements_switchboard_supply_sources = (
        measurements_switchboard_supply_sources or None
    )
    meas.measurements_switchboard_main_breaker = (
        measurements_switchboard_main_breaker or None
    )
    meas.measurements_switchboard_short_circuit_power = (
        measurements_switchboard_short_circuit_power or None
    )
    meas.measurements_switchboard_protection_against_electric_shock = (
        measurements_switchboard_protection_against_electric_shock or None
    )
    meas.measurements_switchboard_external_influences = (
        measurements_switchboard_external_influences or None
    )
    meas.measurements_switchboard_protection_against_overcurrent = (
        measurements_switchboard_protection_against_overcurrent or None
    )
    meas.measurements_switchboard_protection_against_overvoltage = (
        measurements_switchboard_protection_against_overvoltage or None
    )
    meas.measurements_switchboard_overvoltage_category = (
        measurements_switchboard_overvoltage_category or None
    )
    meas.measurements_switchboard_insulation_resistance = (
        measurements_switchboard_insulation_resistance
    )
    meas.measurements_switchboard_loop_impedance = (
        measurements_switchboard_loop_impedance
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
    db.refresh(dev)

    circ = Circuit(
        device_id=dev.device_id,
    )
    db.add(circ)
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
    if not dev:
        return RedirectResponse(url="/revisions", status_code=303)

    switchboard_id = dev.switchboard_id

    db.query(Circuit).filter(Circuit.device_id == device_id).delete()
    db.delete(dev)
    db.commit()
    return RedirectResponse(url=f"/switchboards/{switchboard_id}", status_code=303)


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

    # souhrn kabelu podle koncovych zarizeni
    cable_summary = []
    if circ and circ.terminal_devices:
        agg = {}
        for td in circ.terminal_devices:
            cable = getattr(td, "terminal_device_cable", None)
            installation = getattr(td, "terminal_device_cable_installation_method", None)
            if not cable and not installation:
                continue
            key = (cable or "", installation or "")
            agg[key] = agg.get(key, 0) + 1
        cable_summary = [
            {"cable": k[0], "installation": k[1], "count": v}
            for k, v in agg.items()
        ]

    return templates.TemplateResponse(
        "circuit_detail.html",
        {
            "request": request,
            "circuit": circ,
            "measurement": meas,
            "switchboard": circ.device.switchboard,
            "revision": circ.device.switchboard.revision,
            "cable_summary": cable_summary,
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
    Uložení základních údajů obvodu.
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
    meas.measurements_circuit_earth_resistance = measurements_circuit_earth_resistance
    meas.measurements_circuit_continuity = measurements_circuit_continuity
    meas.measurements_circuit_order_of_phases = (
        measurements_circuit_order_of_phases or None
    )

    db.commit()
    return RedirectResponse(url=f"/circuits/{circuit_id}", status_code=303)



def recompute_circuit_measurement(db: Session, circuit_id: int):
    """
    Přepočet souhrnných hodnot měření obvodu na základě měření koncových zařízení (TerminalMeasurement)
    a aktualizace počtu zásuvek / ks podle koncových zařízení.
    """
    circ = db.query(Circuit).filter(Circuit.circuit_id == circuit_id).first()
    if not circ:
        return

    # Přepočet počtu zásuvek / ks z koncových zařízení
    terminal_devices = (
        db.query(TerminalDevice)
        .filter(TerminalDevice.circuit_id == circuit_id)
        .all()
    )
    total_qty = 0
    for td in terminal_devices:
        if getattr(td, "terminal_device_quantity", None) is not None:
            total_qty += td.terminal_device_quantity or 0
    circ.circuit_number_of_outlets = total_qty or None

    # Přepočet měření z TerminalMeasurement
    terminal_measurements = (
        db.query(TerminalMeasurement)
        .join(TerminalDevice)
        .filter(TerminalDevice.circuit_id == circuit_id)
        .all()
    )

    zs_min_vals = []
    zs_max_vals = []
    t_vals = []
    ir_vals = []
    riso_vals = []

    for tm in terminal_measurements:
        if tm.measurements_circuit_loop_impedance_min is not None:
            zs_min_vals.append(tm.measurements_circuit_loop_impedance_min)
        if tm.measurements_circuit_loop_impedance_max is not None:
            zs_max_vals.append(tm.measurements_circuit_loop_impedance_max)
        if tm.measurements_circuit_rcd_trip_time_ms is not None:
            t_vals.append(tm.measurements_circuit_rcd_trip_time_ms)
        if tm.measurements_circuit_rcd_test_current_ma is not None:
            ir_vals.append(tm.measurements_circuit_rcd_test_current_ma)
        if tm.measurements_circuit_insulation_resistance is not None:
            riso_vals.append(tm.measurements_circuit_insulation_resistance)

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
    terminal_device_quantity: Optional[int] = Form(None),
    terminal_device_power: Optional[float] = Form(None),
    terminal_device_ip_rating: str = Form(""),
    terminal_device_protection_class: str = Form(""),
    terminal_device_serial_number: str = Form(""),
    terminal_device_supply_type: str = Form(""),
    terminal_device_installation_method: str = Form(""),
    terminal_device_cable: str = Form(""),
    terminal_device_cable_installation_method: str = Form(""),
    db: Session = Depends(get_db),
):
    """
    Vytvoření koncového zařízení pro daný obvod.
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

    td = TerminalDevice(
        circuit_id=circuit_id,
        terminal_device_type=terminal_device_type or None,
        terminal_device_manufacturer=terminal_device_manufacturer or None,
        terminal_device_model=terminal_device_model or None,
        terminal_device_marking=terminal_device_marking or None,
        terminal_device_quantity=terminal_device_quantity,
        terminal_device_power=terminal_device_power,
        terminal_device_ip_rating=terminal_device_ip_rating or None,
        terminal_device_protection_class=terminal_device_protection_class or None,
        terminal_device_serial_number=terminal_device_serial_number or None,
        terminal_device_supply_type=terminal_device_supply_type or None,
        terminal_device_installation_method=terminal_device_installation_method or None,
        terminal_device_cable=terminal_device_cable or None,
        terminal_device_cable_installation_method=terminal_device_cable_installation_method or None,
    )
    db.add(td)
    db.commit()

    recompute_circuit_measurement(db, circuit_id)

    return RedirectResponse(url=f"/circuits/{circuit_id}", status_code=303)


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
    if not td:
        return RedirectResponse(url="/revisions", status_code=303)

    circuit_id = td.circuit_id

    db.delete(td)
    db.commit()

    recompute_circuit_measurement(db, circuit_id)

    return RedirectResponse(url=f"/circuits/{circuit_id}", status_code=303)


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

    recompute_circuit_measurement(db, td.circuit_id)

    return RedirectResponse(url=f"/circuits/{td.circuit_id}", status_code=303)
