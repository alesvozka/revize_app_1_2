"""
Testovací skript pro naplnění databáze ukázkovými daty
Spusťte: python seed_data.py
"""
from datetime import date, timedelta
from database import SessionLocal, Base, engine
from models import User, Revision, Switchboard, SwitchboardMeasurement, SwitchboardDevice, Circuit, CircuitMeasurement, TerminalDevice, DropdownSource, DropdownConfig

# Create all tables
Base.metadata.create_all(bind=engine)

def seed_database():
    db = SessionLocal()
    
    try:
        # Check if user already exists
        existing_user = db.query(User).filter(User.user_id == 1).first()
        
        if not existing_user:
            # Create default user
            user = User(
                user_id=1,
                username="admin",
                email="admin@revize-app.cz",
                password_hash="placeholder_hash"  # In production, use proper hashing
            )
            db.add(user)
            db.commit()
            print("✅ Vytvořen uživatel: admin")
        else:
            print("ℹ️  Uživatel admin již existuje")
        
        # Check if revisions already exist
        existing_revisions = db.query(Revision).filter(Revision.user_id == 1).count()
        
        if existing_revisions == 0:
            # Create sample revisions
            revisions = [
                Revision(
                    user_id=1,
                    revision_code="REV-2025-001",
                    revision_name="Revize bytového domu Karlova",
                    revision_owner="Bytové družstvo Karlova",
                    revision_client="BD Karlova",
                    revision_address="Karlova 15, 110 00 Praha 1",
                    revision_description="Pravidelná revize elektroinstalace společných prostor",
                    revision_short_description="Roční pravidelná revize",
                    revision_type="Pravidelná",
                    revision_start_date=date.today() - timedelta(days=5),
                    revision_date_of_creation=date.today() - timedelta(days=10),
                    revision_technician="Jan Novák",
                    revision_certificate_number="CRT-2024-0123",
                    revision_authorization_number="AUTH-456789"
                ),
                Revision(
                    user_id=1,
                    revision_code="REV-2025-002",
                    revision_name="Revize kancelářské budovy TechPark",
                    revision_owner="TechPark s.r.o.",
                    revision_client="TechPark s.r.o.",
                    revision_address="Pražská 234, 120 00 Praha 2",
                    revision_description="Revize po rekonstrukci kanceláří",
                    revision_short_description="Revize po rekonstrukci",
                    revision_type="Mimořádná",
                    revision_start_date=date.today() - timedelta(days=15),
                    revision_end_date=date.today() - timedelta(days=2),
                    revision_date_of_creation=date.today() - timedelta(days=20),
                    revision_technician="Petr Dvořák",
                    revision_certificate_number="CRT-2024-0124",
                    revision_authorization_number="AUTH-456790",
                    revision_overall_assessment="Instalace vyhovuje normám ČSN"
                ),
                Revision(
                    user_id=1,
                    revision_code="REV-2025-003",
                    revision_name="Revize průmyslového areálu Brno",
                    revision_owner="Průmyslové závody Brno a.s.",
                    revision_client="PZ Brno",
                    revision_address="Průmyslová 50, 602 00 Brno",
                    revision_description="Komplexní revize výrobních hal a administrativa",
                    revision_short_description="Výroční revize",
                    revision_type="Pravidelná",
                    revision_start_date=date.today(),
                    revision_date_of_creation=date.today() - timedelta(days=3),
                    revision_recommended_date_for_next_revision=date.today() + timedelta(days=365),
                    revision_technician="Marie Svobodová",
                    revision_certificate_number="CRT-2024-0125",
                    revision_authorization_number="AUTH-456791",
                    revision_number_of_copies_technician=2,
                    revision_number_of_copies_owner=3,
                    revision_number_of_copies_contractor=1,
                    revision_number_of_copies_client=2
                ),
                Revision(
                    user_id=1,
                    revision_code="REV-2024-099",
                    revision_name="Revize rodinného domu Ostrava",
                    revision_owner="Ing. Jiří Procházka",
                    revision_client="Ing. Jiří Procházka",
                    revision_address="Sadová 12, 700 00 Ostrava",
                    revision_description="Revize elektroinstalace rodinného domu",
                    revision_short_description="Pravidelná roční revize",
                    revision_type="Pravidelná",
                    revision_start_date=date.today() - timedelta(days=60),
                    revision_end_date=date.today() - timedelta(days=58),
                    revision_date_of_creation=date.today() - timedelta(days=65),
                    revision_date_of_previous_revision=date.today() - timedelta(days=430),
                    revision_recommended_date_for_next_revision=date.today() + timedelta(days=300),
                    revision_technician="Jan Novák",
                    revision_certificate_number="CRT-2024-0100",
                    revision_authorization_number="AUTH-456788",
                    revision_measuring_instrument_manufacturer_type="FLUKE 1653B",
                    revision_measuring_instrument_serial_number="SN123456789",
                    revision_measuring_instrument_calibration="Kalibrace platná",
                    revision_measuring_instrument_calibration_validity=date.today() + timedelta(days=180),
                    revision_overall_assessment="Elektroinstalace je v dobrém stavu a vyhovuje normám.",
                    revision_number_of_copies_technician=1,
                    revision_number_of_copies_owner=2
                ),
                Revision(
                    user_id=1,
                    revision_code="REV-2025-004",
                    revision_name="Revize školy ZŠ Sluníčko",
                    revision_owner="Město Praha 5",
                    revision_client="ZŠ Sluníčko",
                    revision_address="Školní 789, 150 00 Praha 5",
                    revision_description="Pravidelná revize školní budovy a tělocvičny",
                    revision_short_description="Roční pravidelná revize",
                    revision_type="Pravidelná",
                    revision_start_date=date.today() + timedelta(days=7),
                    revision_date_of_creation=date.today() - timedelta(days=1),
                    revision_technician="Petr Dvořák",
                    revision_certificate_number="CRT-2024-0126"
                )
            ]
            
            for revision in revisions:
                db.add(revision)
            
            db.commit()
            print(f"✅ Vytvořeno {len(revisions)} ukázkových revizí")
        else:
            print(f"ℹ️  Databáze již obsahuje {existing_revisions} revizí")
        
        # Create sample switchboards for first revision
        existing_switchboards = db.query(Switchboard).count()
        
        if existing_switchboards == 0:
            # Get first revision
            first_revision = db.query(Revision).filter(Revision.user_id == 1).first()
            
            if first_revision:
                switchboards = [
                    Switchboard(
                        revision_id=first_revision.revision_id,
                        switchboard_name="Hlavní rozváděč přízemí",
                        switchboard_location="Chodba u vchodu",
                        switchboard_order=1,
                        switchboard_type="Přístrojová skříň",
                        switchboard_serial_number="HR-2024-001",
                        switchboard_production_date=date(2023, 5, 15),
                        switchboard_ip_rating="IP40",
                        switchboard_impact_protection="IK07",
                        switchboard_protection_class="I",
                        switchboard_rated_current=63.0,
                        switchboard_rated_voltage=400.0,
                        switchboard_manufacturer="ABB s.r.o.",
                        switchboard_standards="ČSN EN 61439-1, ČSN EN 61439-2",
                        switchboard_enclosure_type="Nástěnná",
                        switchboard_enclosure_manufacturer="ABB",
                        switchboard_enclosure_installation_method="Nástěnná montáž",
                        switchboard_superior_switchboard="Hlavní jistič objektu",
                        switchboard_superior_circuit_breaker_rated_current=80.0,
                        switchboard_superior_circuit_breaker_trip_characteristic="C",
                        switchboard_superior_circuit_breaker_manufacturer="ABB",
                        switchboard_superior_circuit_breaker_model="S203-C80",
                        switchboard_main_switch="Hlavní vypínač 63A",
                        switchboard_cable="CYKY 5x16",
                        switchboard_cable_installation_method="V zemi"
                    ),
                    Switchboard(
                        revision_id=first_revision.revision_id,
                        switchboard_name="Podružný rozváděč 1.NP",
                        switchboard_location="Technická místnost 1.NP",
                        switchboard_order=2,
                        switchboard_type="Podružný rozváděč",
                        switchboard_serial_number="PR1-2024-002",
                        switchboard_ip_rating="IP30",
                        switchboard_protection_class="I",
                        switchboard_rated_current=40.0,
                        switchboard_rated_voltage=230.0,
                        switchboard_manufacturer="Siemens",
                        switchboard_enclosure_type="Vestavěná",
                        switchboard_superior_switchboard="Hlavní rozváděč přízemí",
                        switchboard_superior_circuit_breaker_rated_current=50.0,
                        switchboard_superior_circuit_breaker_trip_characteristic="B",
                        switchboard_cable="CYKY 5x10"
                    ),
                    Switchboard(
                        revision_id=first_revision.revision_id,
                        switchboard_name="Rozváděč suterén",
                        switchboard_location="Sklep - společné prostory",
                        switchboard_order=3,
                        switchboard_type="Přístrojová skříň",
                        switchboard_ip_rating="IP44",
                        switchboard_rated_current=32.0,
                        switchboard_rated_voltage=230.0,
                        switchboard_manufacturer="Schneider Electric",
                        switchboard_note="Vlhké prostředí - zvýšené krytí IP44"
                    )
                ]
                
                for switchboard in switchboards:
                    db.add(switchboard)
                
                db.commit()
                print(f"✅ Vytvořeno {len(switchboards)} ukázkových rozváděčů")
            else:
                print("⚠️  Nelze vytvořit switchboardy - revize neexistuje")
        else:
            print(f"ℹ️  Databáze již obsahuje {existing_switchboards} rozváděčů")
        
        # Create sample measurements for first two switchboards
        existing_measurements = db.query(SwitchboardMeasurement).count()
        
        if existing_measurements == 0:
            # Get first two switchboards
            switchboards = db.query(Switchboard).limit(2).all()
            
            if len(switchboards) >= 2:
                measurements = [
                    SwitchboardMeasurement(
                        switchboard_id=switchboards[0].switchboard_id,
                        measurements_switchboard_insulation_resistance=500.0,
                        measurements_switchboard_loop_impedance_min=0.15,
                        measurements_switchboard_loop_impedance_max=0.25,
                        measurements_switchboard_rcd_trip_time_ms=25.0,
                        measurements_switchboard_rcd_test_current_ma=30.0,
                        measurements_switchboard_earth_resistance=5.2
                    ),
                    SwitchboardMeasurement(
                        switchboard_id=switchboards[1].switchboard_id,
                        measurements_switchboard_insulation_resistance=450.0,
                        measurements_switchboard_loop_impedance_min=0.18,
                        measurements_switchboard_loop_impedance_max=0.28,
                        measurements_switchboard_rcd_trip_time_ms=28.0,
                        measurements_switchboard_rcd_test_current_ma=30.0,
                        measurements_switchboard_earth_resistance=6.1
                    )
                ]
                
                for measurement in measurements:
                    db.add(measurement)
                
                db.commit()
                print(f"✅ Vytvořeno {len(measurements)} ukázkových měření")
            else:
                print("⚠️  Nelze vytvořit měření - nedostatek switchboardů")
        else:
            print(f"ℹ️  Databáze již obsahuje {existing_measurements} měření")
        
        # Create sample devices for first switchboard with hierarchy
        existing_devices = db.query(SwitchboardDevice).count()
        
        if existing_devices == 0:
            # Get first switchboard
            first_switchboard = db.query(Switchboard).first()
            
            if first_switchboard:
                # Create RCD (parent device)
                rcd1 = SwitchboardDevice(
                    switchboard_id=first_switchboard.switchboard_id,
                    parent_device_id=None,  # Root device
                    switchboard_device_position="1-4",
                    switchboard_device_type="RCD",
                    switchboard_device_manufacturer="ABB",
                    switchboard_device_model="F204 AC-40/0.03",
                    switchboard_device_rated_current=40.0,
                    switchboard_device_residual_current_ma=30.0,
                    switchboard_device_poles=4,
                    switchboard_device_module_width=4.0
                )
                db.add(rcd1)
                db.flush()  # Get ID for parent reference
                
                # Create MCBs under RCD
                mcb1 = SwitchboardDevice(
                    switchboard_id=first_switchboard.switchboard_id,
                    parent_device_id=rcd1.device_id,
                    switchboard_device_position="5",
                    switchboard_device_type="MCB",
                    switchboard_device_manufacturer="ABB",
                    switchboard_device_model="S201-B16",
                    switchboard_device_trip_characteristic="B",
                    switchboard_device_rated_current=16.0,
                    switchboard_device_poles=1,
                    switchboard_device_module_width=1.0
                )
                db.add(mcb1)
                
                mcb2 = SwitchboardDevice(
                    switchboard_id=first_switchboard.switchboard_id,
                    parent_device_id=rcd1.device_id,
                    switchboard_device_position="6",
                    switchboard_device_type="MCB",
                    switchboard_device_manufacturer="ABB",
                    switchboard_device_model="S201-C20",
                    switchboard_device_trip_characteristic="C",
                    switchboard_device_rated_current=20.0,
                    switchboard_device_poles=1,
                    switchboard_device_module_width=1.0
                )
                db.add(mcb2)
                
                # Create another RCD
                rcd2 = SwitchboardDevice(
                    switchboard_id=first_switchboard.switchboard_id,
                    parent_device_id=None,
                    switchboard_device_position="7-10",
                    switchboard_device_type="RCD",
                    switchboard_device_manufacturer="Schneider Electric",
                    switchboard_device_model="iID 40A 30mA AC",
                    switchboard_device_rated_current=40.0,
                    switchboard_device_residual_current_ma=30.0,
                    switchboard_device_poles=4,
                    switchboard_device_module_width=4.0
                )
                db.add(rcd2)
                db.flush()
                
                # Create MCB under second RCD
                mcb3 = SwitchboardDevice(
                    switchboard_id=first_switchboard.switchboard_id,
                    parent_device_id=rcd2.device_id,
                    switchboard_device_position="11",
                    switchboard_device_type="MCB",
                    switchboard_device_manufacturer="Schneider Electric",
                    switchboard_device_model="iC60N B10",
                    switchboard_device_trip_characteristic="B",
                    switchboard_device_rated_current=10.0,
                    switchboard_device_poles=1,
                    switchboard_device_module_width=1.0
                )
                db.add(mcb3)
                db.flush()
                
                # Create sub-device (contactor) under MCB
                contactor = SwitchboardDevice(
                    switchboard_id=first_switchboard.switchboard_id,
                    parent_device_id=mcb3.device_id,
                    switchboard_device_position="12-13",
                    switchboard_device_type="Stykač",
                    switchboard_device_manufacturer="Schneider Electric",
                    switchboard_device_model="LC1D09",
                    switchboard_device_rated_current=9.0,
                    switchboard_device_poles=3,
                    switchboard_device_module_width=2.0,
                    switchboard_device_sub_devices="Motor 2.2kW"
                )
                db.add(contactor)
                
                db.commit()
                print(f"✅ Vytvořeno 7 ukázkových přístrojů s hierarchií (2 RCD → 3 MCB → 1 Stykač)")
                
                # ============================================================================
                # CREATE SAMPLE CIRCUITS (OBVODY)
                # ============================================================================
                
                existing_circuits = db.query(Circuit).count()
                
                if existing_circuits == 0:
                    # Circuit 1: Connected to MCB1 (B16)
                    circuit1 = Circuit(
                        device_id=mcb1.device_id,
                        circuit_number="1",
                        circuit_room="Kuchyně",
                        circuit_description="Zásuvkový obvod kuchyně - lednice, mikrovlnka, el. trouba",
                        circuit_description_from_switchboard="Kuchyně zásuvky",
                        circuit_number_of_outlets=4,
                        circuit_cable="CYKY 3×2,5",
                        circuit_cable_installation_method="Pod omítkou",
                        circuit_cable_termination="Zásuvky"
                    )
                    db.add(circuit1)
                    db.flush()  # Get circuit_id for measurement
                    
                    # Add measurement for circuit1
                    meas1 = CircuitMeasurement(
                        circuit_id=circuit1.circuit_id,
                        measurements_circuit_insulation_resistance=520.5,
                        measurements_circuit_loop_impedance_min=0.215,
                        measurements_circuit_loop_impedance_max=0.285,
                        measurements_circuit_rcd_trip_time_ms=24.5,
                        measurements_circuit_rcd_test_current_ma=30.0,
                        measurements_circuit_earth_resistance=0.125,
                        measurements_circuit_continuity=0.045,
                        measurements_circuit_order_of_phases="L1-L2-L3"
                    )
                    db.add(meas1)
                    
                    # Circuit 2: Connected to MCB1 (same device, different circuit)
                    circuit2 = Circuit(
                        device_id=mcb1.device_id,
                        circuit_number="2",
                        circuit_room="Obývací pokoj",
                        circuit_description="Zásuvkový obvod obýváku - TV, audio systém, osvětlení",
                        circuit_description_from_switchboard="Obývák zásuvky",
                        circuit_number_of_outlets=6,
                        circuit_cable="CYKY 3×2,5",
                        circuit_cable_installation_method="Pod omítkou",
                        circuit_cable_termination="Zásuvky"
                    )
                    db.add(circuit2)
                    db.flush()
                    
                    # Add measurement for circuit2
                    meas2 = CircuitMeasurement(
                        circuit_id=circuit2.circuit_id,
                        measurements_circuit_insulation_resistance=485.2,
                        measurements_circuit_loop_impedance_min=0.198,
                        measurements_circuit_loop_impedance_max=0.267,
                        measurements_circuit_rcd_trip_time_ms=26.8,
                        measurements_circuit_rcd_test_current_ma=30.0,
                        measurements_circuit_earth_resistance=0.118,
                        measurements_circuit_continuity=0.038,
                        measurements_circuit_order_of_phases="L1-L2-L3"
                    )
                    db.add(meas2)
                    
                    # Circuit 3: Connected to MCB2 (C20)
                    circuit3 = Circuit(
                        device_id=mcb2.device_id,
                        circuit_number="3",
                        circuit_room="Koupelna",
                        circuit_description="Koupelna - bojler, pračka, osvětlení",
                        circuit_description_from_switchboard="Koupelna",
                        circuit_number_of_outlets=2,
                        circuit_cable="CYKY 3×2,5",
                        circuit_cable_installation_method="Pod omítkou",
                        circuit_cable_termination="Zásuvky + bojler"
                    )
                    db.add(circuit3)
                    db.flush()
                    
                    # Add measurement for circuit3
                    meas3 = CircuitMeasurement(
                        circuit_id=circuit3.circuit_id,
                        measurements_circuit_insulation_resistance=395.8,
                        measurements_circuit_loop_impedance_min=0.245,
                        measurements_circuit_loop_impedance_max=0.315,
                        measurements_circuit_rcd_trip_time_ms=22.1,
                        measurements_circuit_rcd_test_current_ma=30.0,
                        measurements_circuit_earth_resistance=0.142,
                        measurements_circuit_continuity=0.052,
                        measurements_circuit_order_of_phases="L1-L2-L3"
                    )
                    db.add(meas3)
                    
                    # Circuit 4: Connected to MCB3 (B10) - before contactor
                    circuit4 = Circuit(
                        device_id=mcb3.device_id,
                        circuit_number="4",
                        circuit_room="Chodba",
                        circuit_description="Osvětlení společných prostor - chodba, schodiště",
                        circuit_description_from_switchboard="Osvětlení chodba",
                        circuit_number_of_outlets=0,
                        circuit_cable="CYKY 3×1,5",
                        circuit_cable_installation_method="V elektroinstalační liště",
                        circuit_cable_termination="Svítidla LED"
                    )
                    db.add(circuit4)
                    # No measurement for this one - to show empty state
                    
                    # Circuit 5: Connected to Contactor (Motor circuit)
                    circuit5 = Circuit(
                        device_id=contactor.device_id,
                        circuit_number="M1",
                        circuit_room="Technická místnost",
                        circuit_description="Elektromotor čerpadla - TUV ohřev",
                        circuit_description_from_switchboard="Motor čerpadlo TUV",
                        circuit_number_of_outlets=0,
                        circuit_cable="CYKY 5×2,5",
                        circuit_cable_installation_method="V chráničce",
                        circuit_cable_termination="Motor 2.2kW"
                    )
                    db.add(circuit5)
                    db.flush()
                    
                    # Add measurement for circuit5
                    meas5 = CircuitMeasurement(
                        circuit_id=circuit5.circuit_id,
                        measurements_circuit_insulation_resistance=625.3,
                        measurements_circuit_loop_impedance_min=0.185,
                        measurements_circuit_loop_impedance_max=0.225,
                        measurements_circuit_earth_resistance=0.095,
                        measurements_circuit_continuity=0.028,
                        measurements_circuit_order_of_phases="L1-L2-L3"
                    )
                    db.add(meas5)
                    
                    db.commit()
                    print(f"✅ Vytvořeno 5 ukázkových obvodů s měřeními (4 obvody s měřením, 1 bez)")
                    
                    # ============================================================================
                    # CREATE SAMPLE TERMINAL DEVICES (KONCOVÁ ZAŘÍZENÍ)
                    # ============================================================================
                    
                    existing_terminals = db.query(TerminalDevice).count()
                    
                    if existing_terminals == 0:
                        # Terminal 1: LED světlo v kuchyni (Circuit 1)
                        terminal1 = TerminalDevice(
                            circuit_id=circuit1.circuit_id,
                            terminal_device_type="Světlo LED",
                            terminal_device_manufacturer="Philips",
                            terminal_device_model="LED Panel 600x600",
                            terminal_device_marking="L1",
                            terminal_device_power=40.0,
                            terminal_device_ip_rating="IP20",
                            terminal_device_protection_class="I",
                            terminal_device_supply_type="230V AC",
                            terminal_device_installation_method="Stropní vestavné"
                        )
                        db.add(terminal1)
                        
                        # Terminal 2: Lednice v kuchyni (Circuit 1)
                        terminal2 = TerminalDevice(
                            circuit_id=circuit1.circuit_id,
                            terminal_device_type="Lednice",
                            terminal_device_manufacturer="Samsung",
                            terminal_device_model="RB34T632ESA",
                            terminal_device_marking="Z1",
                            terminal_device_power=150.0,
                            terminal_device_ip_rating="IP20",
                            terminal_device_protection_class="I",
                            terminal_device_serial_number="2024-KR-78945",
                            terminal_device_supply_type="230V AC",
                            terminal_device_installation_method="Volně stojící"
                        )
                        db.add(terminal2)
                        
                        # Terminal 3: TV v obýváku (Circuit 2)
                        terminal3 = TerminalDevice(
                            circuit_id=circuit2.circuit_id,
                            terminal_device_type="Televize",
                            terminal_device_manufacturer="LG",
                            terminal_device_model="OLED55C3",
                            terminal_device_marking="TV1",
                            terminal_device_power=120.0,
                            terminal_device_ip_rating="IP20",
                            terminal_device_protection_class="II",
                            terminal_device_serial_number="2024-LG-55432",
                            terminal_device_supply_type="230V AC",
                            terminal_device_installation_method="Nástěnné"
                        )
                        db.add(terminal3)
                        
                        # Terminal 4: Bojler v koupelně (Circuit 3)
                        terminal4 = TerminalDevice(
                            circuit_id=circuit3.circuit_id,
                            terminal_device_type="Bojler",
                            terminal_device_manufacturer="Dražice",
                            terminal_device_model="OKCE 80",
                            terminal_device_marking="B1",
                            terminal_device_power=2000.0,
                            terminal_device_ip_rating="IP24",
                            terminal_device_protection_class="I",
                            terminal_device_serial_number="2023-DR-12389",
                            terminal_device_supply_type="230V AC",
                            terminal_device_installation_method="Nástěnné"
                        )
                        db.add(terminal4)
                        
                        # Terminal 5: Pračka v koupelně (Circuit 3)
                        terminal5 = TerminalDevice(
                            circuit_id=circuit3.circuit_id,
                            terminal_device_type="Pračka",
                            terminal_device_manufacturer="Bosch",
                            terminal_device_model="WAU28T64BY",
                            terminal_device_marking="P1",
                            terminal_device_power=1400.0,
                            terminal_device_ip_rating="IPX4",
                            terminal_device_protection_class="I",
                            terminal_device_serial_number="2024-BS-98765",
                            terminal_device_supply_type="230V AC",
                            terminal_device_installation_method="Volně stojící"
                        )
                        db.add(terminal5)
                        
                        # Terminal 6: LED panel v chodbě (Circuit 4)
                        terminal6 = TerminalDevice(
                            circuit_id=circuit4.circuit_id,
                            terminal_device_type="Světlo LED",
                            terminal_device_manufacturer="ABB",
                            terminal_device_model="LED Panel 300x1200",
                            terminal_device_marking="L2",
                            terminal_device_power=36.0,
                            terminal_device_ip_rating="IP20",
                            terminal_device_protection_class="II",
                            terminal_device_supply_type="230V AC",
                            terminal_device_installation_method="Stropní vestavné"
                        )
                        db.add(terminal6)
                        
                        # Terminal 7: Motor čerpadla (Circuit 5)
                        terminal7 = TerminalDevice(
                            circuit_id=circuit5.circuit_id,
                            terminal_device_type="Elektromotor",
                            terminal_device_manufacturer="Siemens",
                            terminal_device_model="1LE1001-1CA23-4AA4",
                            terminal_device_marking="M1",
                            terminal_device_power=2200.0,
                            terminal_device_ip_rating="IP55",
                            terminal_device_protection_class="I",
                            terminal_device_serial_number="2024-SI-45678",
                            terminal_device_supply_type="3×400V AC",
                            terminal_device_installation_method="Nožkové"
                        )
                        db.add(terminal7)
                        
                        db.commit()
                        print(f"✅ Vytvořeno 7 ukázkových koncových zařízení (světla, spotřebiče, motor)")
                    else:
                        print(f"ℹ️  Databáze již obsahuje {existing_terminals} koncových zařízení")
                    
                    # ============================================================================
                    # CREATE SAMPLE DROPDOWN DATA
                    # ============================================================================
                    
                    existing_dropdowns = db.query(DropdownSource).count()
                    
                    if existing_dropdowns == 0:
                        # Category: Manufacturers (Výrobci)
                        manufacturers = [
                            "ABB", "Schneider Electric", "Siemens", "Legrand", "Eaton",
                            "Hager", "OEZ", "Moeller", "Phoenix Contact", "WAGO"
                        ]
                        for i, name in enumerate(manufacturers):
                            db.add(DropdownSource(
                                category="vyrobci",
                                value=name,
                                display_order=i
                            ))
                        
                        # Category: Cable Types (Typy kabelů)
                        cables = [
                            "CYKY 3×1,5", "CYKY 3×2,5", "CYKY 3×4", "CYKY 3×6",
                            "CYKY 5×1,5", "CYKY 5×2,5", "CYKY 5×4",
                            "NYM 3×1,5", "NYM 3×2,5", "NYM 5×1,5", "NYM 5×2,5",
                            "CYKY-J 3×1,5", "CYKY-J 3×2,5", "CYKY-J 5×2,5"
                        ]
                        for i, cable in enumerate(cables):
                            db.add(DropdownSource(
                                category="typy_kabelu",
                                value=cable,
                                display_order=i
                            ))
                        
                        # Category: Installation Methods (Způsoby uložení)
                        methods = [
                            "Pod omítkou", "Na omítce", "V elektroinstalační liště",
                            "V chráničce", "Volně vedeném", "Na kabelových žlabech",
                            "V instalační trubce", "Na cable trays"
                        ]
                        for i, method in enumerate(methods):
                            db.add(DropdownSource(
                                category="zpusoby_ulozeni",
                                value=method,
                                display_order=i
                            ))
                        
                        # Category: Device Types (Typy přístrojů)
                        device_types = [
                            "RCD (Proudový chránič)", "MCB (Jistič)", "RCBO (Kombinovaný jistič)",
                            "Stykač", "Motorový spouštěč", "Pojistkový odpínač",
                            "Hlavní vypínač", "Přepěťová ochrana", "Kontrolka"
                        ]
                        for i, dtype in enumerate(device_types):
                            db.add(DropdownSource(
                                category="typy_pristroju",
                                value=dtype,
                                display_order=i
                            ))
                        
                        # Category: Trip Characteristics (Vypínací charakteristiky)
                        characteristics = ["B", "C", "D", "K", "Z"]
                        for i, char in enumerate(characteristics):
                            db.add(DropdownSource(
                                category="vypinaci_charakteristiky",
                                value=char,
                                display_order=i
                            ))
                        
                        # Category: IP Ratings (Stupně krytí)
                        ip_ratings = [
                            "IP20", "IP21", "IP22", "IP23", "IP24",
                            "IP44", "IP54", "IP55", "IP65", "IP66", "IP67", "IP68",
                            "IPX4", "IPX5"
                        ]
                        for i, ip in enumerate(ip_ratings):
                            db.add(DropdownSource(
                                category="stupen_kryti",
                                value=ip,
                                display_order=i
                            ))
                        
                        # Category: Protection Classes (Třídy ochrany)
                        protection_classes = ["I", "II", "III"]
                        for i, pclass in enumerate(protection_classes):
                            db.add(DropdownSource(
                                category="tridy_ochrany",
                                value=pclass,
                                display_order=i
                            ))
                        
                        # Category: Terminal Device Types (Typy koncových zařízení)
                        terminal_types = [
                            "Světlo LED", "Světlo žárovkové", "Světlo zářivkové",
                            "Zásuvka", "Vypínač", "Spínač",
                            "Lednice", "Pračka", "Bojler", "Myčka",
                            "Televize", "Počítač",
                            "Motor", "Ventilátor", "Čerpadlo"
                        ]
                        for i, ttype in enumerate(terminal_types):
                            db.add(DropdownSource(
                                category="typy_konc_zarizeni",
                                value=ttype,
                                display_order=i
                            ))
                        
                        db.commit()
                        print(f"✅ Vytvořeno 8 kategorií dropdownů s cca 80 hodnotami")
                    else:
                        print(f"ℹ️  Databáze již obsahuje {existing_dropdowns} dropdown hodnot")
                    
                else:
                    print(f"ℹ️  Databáze již obsahuje {existing_circuits} obvodů")
                
            else:
                print("⚠️  Nelze vytvořit přístroje - switchboard neexistuje")
        else:
            print(f"ℹ️  Databáze již obsahuje {existing_devices} přístrojů")
        
        print("\n🎉 Databáze je připravena k použití!")
        print("   Přihlaste se jako uživatel: admin")
        print("   Pro zobrazení dashboardu běžte na: http://localhost:8000")
        
    except Exception as e:
        print(f"❌ Chyba při naplňování databáze: {e}")
        db.rollback()
    finally:
        db.close()


if __name__ == "__main__":
    print("🚀 Zahajuji naplnění databáze testovacími daty...\n")
    seed_database()
