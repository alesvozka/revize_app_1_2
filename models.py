from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Boolean, ForeignKey, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from database import Base


# 1. USERS
class User(Base):
    __tablename__ = "users"

    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    revisions = relationship("Revision", back_populates="user")


# 2. REVISIONS
class Revision(Base):
    __tablename__ = "revisions"

    revision_id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.user_id"), nullable=False)

    revision_code = Column(String(100))
    revision_name = Column(String(255))
    revision_owner = Column(String(255))
    revision_client = Column(String(255))
    revision_address = Column(Text)
    revision_description = Column(Text)
    revision_type = Column(String(100))
    revision_date_of_previous_revision = Column(Date)
    revision_start_date = Column(Date)
    revision_end_date = Column(Date)
    revision_date_of_creation = Column(Date)
    revision_recommended_date_for_next_revision = Column(Date)
    revision_number_of_copies_technician = Column(Integer)
    revision_number_of_copies_owner = Column(Integer)
    revision_number_of_copies_contractor = Column(Integer)
    revision_number_of_copies_client = Column(Integer)
    revision_attachment = Column(String(255))
    revision_attachment_submitter = Column(String(255))
    revision_attachment_producer = Column(String(255))
    revision_attachment_date_of_creation = Column(Date)
    revision_technician = Column(String(255))
    revision_certificate_number = Column(String(100))
    revision_authorization_number = Column(String(100))
    revision_project_documentation = Column(Text)
    revision_contractor = Column(String(255))
    revision_short_description = Column(Text)
    revision_measuring_instrument_manufacturer_type = Column(String(255))
    revision_measuring_instrument_serial_number = Column(String(100))
    revision_measuring_instrument_calibration = Column(String(255))
    revision_measuring_instrument_calibration_validity = Column(Date)
    revision_overall_assessment = Column(Text)

    # Relationships
    user = relationship("User", back_populates="revisions")
    switchboards = relationship("Switchboard", back_populates="revision", cascade="all, delete-orphan")


# 3. SWITCHBOARDS
class Switchboard(Base):
    __tablename__ = "switchboards"

    switchboard_id = Column(Integer, primary_key=True, index=True)
    revision_id = Column(Integer, ForeignKey("revisions.revision_id"), nullable=False)

    switchboard_name = Column(String(255))
    switchboard_description = Column(Text)
    switchboard_location = Column(String(255))
    switchboard_order = Column(Integer, default=0)
    switchboard_type = Column(String(100))
    switchboard_serial_number = Column(String(100))
    switchboard_production_date = Column(Date)
    switchboard_ip_rating = Column(String(50))
    switchboard_impact_protection = Column(String(50))
    switchboard_protection_class = Column(String(50))
    switchboard_rated_current = Column(Float)
    switchboard_rated_voltage = Column(Float)
    switchboard_manufacturer = Column(String(255))
    switchboard_manufacturer_address = Column(Text)
    switchboard_standards = Column(Text)
    switchboard_enclosure_type = Column(String(100))
    switchboard_enclosure_manufacturer = Column(String(255))
    switchboard_enclosure_installation_method = Column(String(255))
    switchboard_superior_switchboard = Column(String(255))
    switchboard_superior_circuit_breaker_rated_current = Column(Float)
    switchboard_superior_circuit_breaker_trip_characteristic = Column(String(50))
    switchboard_superior_circuit_breaker_manufacturer = Column(String(255))
    switchboard_superior_circuit_breaker_model = Column(String(100))
    switchboard_main_switch = Column(String(255))
    switchboard_note = Column(Text)
    switchboard_cable = Column(String(255))
    switchboard_cable_installation_method = Column(String(255))

    # Relationships
    revision = relationship("Revision", back_populates="switchboards")
    measurements = relationship("SwitchboardMeasurement", back_populates="switchboard", uselist=False, cascade="all, delete-orphan")
    devices = relationship("SwitchboardDevice", back_populates="switchboard", cascade="all, delete-orphan")


# 4. SWITCHBOARD_MEASUREMENTS
class SwitchboardMeasurement(Base):
    __tablename__ = "switchboard_measurements"

    measurement_id = Column(Integer, primary_key=True, index=True)
    switchboard_id = Column(Integer, ForeignKey("switchboards.switchboard_id"), unique=True, nullable=False)

    measurements_switchboard_insulation_resistance = Column(Float)
    measurements_switchboard_loop_impedance_min = Column(Float)
    measurements_switchboard_loop_impedance_max = Column(Float)
    measurements_switchboard_rcd_trip_time_ms = Column(Float)
    measurements_switchboard_rcd_test_current_ma = Column(Float)
    measurements_switchboard_earth_resistance = Column(Float)

    # Relationships
    switchboard = relationship("Switchboard", back_populates="measurements")


# 5. SWITCHBOARD_DEVICES
class SwitchboardDevice(Base):
    __tablename__ = "switchboard_devices"

    device_id = Column(Integer, primary_key=True, index=True)
    switchboard_id = Column(Integer, ForeignKey("switchboards.switchboard_id"), nullable=False)
    parent_device_id = Column(Integer, ForeignKey("switchboard_devices.device_id"), nullable=True)

    switchboard_device_position = Column(String(100))
    switchboard_device_type = Column(String(100))
    switchboard_device_manufacturer = Column(String(255))
    switchboard_device_model = Column(String(100))
    switchboard_device_trip_characteristic = Column(String(50))
    switchboard_device_rated_current = Column(Float)
    switchboard_device_residual_current_ma = Column(Float)
    switchboard_device_sub_devices = Column(Text)
    switchboard_device_poles = Column(Integer)
    switchboard_device_module_width = Column(Float)

    # Relationships
    switchboard = relationship("Switchboard", back_populates="devices")
    parent_device = relationship("SwitchboardDevice", remote_side=[device_id], backref="child_devices")
    circuits = relationship("Circuit", back_populates="device", cascade="all, delete-orphan")


# 6. CIRCUITS
class Circuit(Base):
    __tablename__ = "circuits"

    circuit_id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("switchboard_devices.device_id"), nullable=False)

    circuit_number = Column(String(100))
    circuit_room = Column(String(255))
    circuit_description = Column(Text)
    circuit_description_from_switchboard = Column(Text)
    circuit_number_of_outlets = Column(Integer)
    circuit_cable_termination = Column(String(255))
    circuit_cable = Column(String(255))
    circuit_cable_installation_method = Column(String(255))

    # Relationships
    device = relationship("SwitchboardDevice", back_populates="circuits")
    measurements = relationship("CircuitMeasurement", back_populates="circuit", uselist=False, cascade="all, delete-orphan")
    terminal_devices = relationship("TerminalDevice", back_populates="circuit", cascade="all, delete-orphan")


# 7. CIRCUIT_MEASUREMENTS
class CircuitMeasurement(Base):
    __tablename__ = "circuit_measurements"

    measurement_id = Column(Integer, primary_key=True, index=True)
    circuit_id = Column(Integer, ForeignKey("circuits.circuit_id"), unique=True, nullable=False)

    measurements_circuit_insulation_resistance = Column(Float)
    measurements_circuit_loop_impedance_min = Column(Float)
    measurements_circuit_loop_impedance_max = Column(Float)
    measurements_circuit_rcd_trip_time_ms = Column(Float)
    measurements_circuit_rcd_test_current_ma = Column(Float)
    measurements_circuit_earth_resistance = Column(Float)
    measurements_circuit_continuity = Column(Float)
    measurements_circuit_order_of_phases = Column(String(50))

    # Relationships
    circuit = relationship("Circuit", back_populates="measurements")


# 8. TERMINAL_DEVICES
class TerminalDevice(Base):
    __tablename__ = "terminal_devices"

    terminal_device_id = Column(Integer, primary_key=True, index=True)
    circuit_id = Column(Integer, ForeignKey("circuits.circuit_id"), nullable=False)

    terminal_device_type = Column(String(100))
    terminal_device_manufacturer = Column(String(255))
    terminal_device_model = Column(String(100))
    terminal_device_marking = Column(String(100))
    terminal_device_power = Column(Float)
    terminal_device_ip_rating = Column(String(50))
    terminal_device_protection_class = Column(String(50))
    terminal_device_serial_number = Column(String(100))
    terminal_device_supply_type = Column(String(100))
    terminal_device_installation_method = Column(String(255))
    terminal_device_cable = Column(String(255))
    terminal_device_cable_installation_method = Column(String(255))


    # Relationships
    circuit = relationship("Circuit", back_populates="terminal_devices")
    measurements = relationship(
        "TerminalMeasurement",
        back_populates="terminal_device",
        uselist=False,
        cascade="all, delete-orphan",
    )


class TerminalMeasurement(Base):
    __tablename__ = "terminal_measurements"

    measurement_id = Column(Integer, primary_key=True, index=True)
    terminal_device_id = Column(
        Integer,
        ForeignKey("terminal_devices.terminal_device_id"),
        unique=True,
        nullable=False,
    )

    # Měření na úrovni koncového zařízení / skupiny zařízení
    measurements_circuit_insulation_resistance = Column(Float)
    measurements_circuit_loop_impedance_min = Column(Float)
    measurements_circuit_loop_impedance_max = Column(Float)
    measurements_circuit_rcd_trip_time_ms = Column(Float)
    measurements_circuit_rcd_test_current_ma = Column(Float)

    # Relationships
    terminal_device = relationship("TerminalDevice", back_populates="measurements")


# 9. DROPDOWN_SOURCES
class DropdownSource(Base):
    __tablename__ = "dropdown_sources"

    id = Column(Integer, primary_key=True, index=True)
    category = Column(String(100), nullable=False, index=True)
    value = Column(String(255), nullable=False)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


# 10. DROPDOWN_CONFIG
class DropdownConfig(Base):
    __tablename__ = "dropdown_config"

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(100), nullable=False)
    field_name = Column(String(255), nullable=False)
    dropdown_enabled = Column(Boolean, default=False)
    dropdown_category = Column(String(100), nullable=True)

    # PHASE 4: Field visibility and configuration
    field_label = Column(String(255), nullable=True)  # Display label
    field_category = Column(String(100), nullable=True)  # 'basic', 'additional', 'measurements'
    display_order = Column(Integer, default=0)  # Display order in forms
    enabled = Column(Boolean, default=True)  # Field visibility
    is_required = Column(Boolean, default=False)  # Is field required?
    field_type = Column(String(50), default='text')  # 'text', 'number', 'date', 'textarea'

    # PHASE 4.5: Custom label for field renaming
    custom_label = Column(String(255), nullable=True)  # User-defined label override


# 11. FIELD_CATEGORIES (PHASE 4.5)
class FieldCategory(Base):
    __tablename__ = "field_categories"
    __table_args__ = (
        # Zajistí, že každá kombinace entity_type + category_key je unikátní
        UniqueConstraint('entity_type', 'category_key', name='uix_entity_category'),
    )

    id = Column(Integer, primary_key=True, index=True)
    entity_type = Column(String(100), nullable=False)
    category_key = Column(String(100), nullable=False)
    category_label = Column(String(255), nullable=False)
    display_order = Column(Integer, default=0)
    icon = Column(String(50), default='📋')
    created_at = Column(DateTime(timezone=True), server_default=func.now())
