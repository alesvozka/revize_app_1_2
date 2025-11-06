"""
Testovací skript pro naplnění databáze ukázkovými daty
Spusťte: python seed_data.py
"""
from datetime import date, timedelta
from database import SessionLocal, Base, engine
from models import User, Revision, Switchboard, SwitchboardMeasurement

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
