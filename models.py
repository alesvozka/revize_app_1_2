from sqlalchemy import Column, Integer, String, Text, Date, DateTime, Boolean, ForeignKey, Float
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    revisions = relationship("Revision", back_populates="user", cascade="all, delete-orphan")


class Revision(Base):
    __tablename__ = "revisions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    location = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    user = relationship("User", back_populates="revisions")
    switchboards = relationship("Switchboard", back_populates="revision", cascade="all, delete-orphan", order_by="Switchboard.display_order")


class Switchboard(Base):
    __tablename__ = "switchboards"

    id = Column(Integer, primary_key=True, index=True)
    revision_id = Column(Integer, ForeignKey("revisions.id"), nullable=False)

    name = Column(String(255), nullable=False)
    code = Column(String(100), nullable=True)
    location = Column(String(255), nullable=True)
    note = Column(Text, nullable=True)
    display_order = Column(Integer, default=0)

    # basic technical fields
    supply_voltage = Column(Float, nullable=True)
    rated_current = Column(Float, nullable=True)
    short_circuit_level = Column(Float, nullable=True)

    revision = relationship("Revision", back_populates="switchboards")
    devices = relationship("Device", back_populates="switchboard", cascade="all, delete-orphan", order_by="Device.row_order")


class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    switchboard_id = Column(Integer, ForeignKey("switchboards.id"), nullable=False)

    row_order = Column(Integer, default=0)
    label = Column(String(100), nullable=True)        # např. jistič č.
    description = Column(Text, nullable=True)         # název obvodu
    breaker_type = Column(String(50), nullable=True)  # MCB/RCD/RCBO/...
    characteristic = Column(String(10), nullable=True) # B/C/D/...
    rated_current = Column(Float, nullable=True)
    poles = Column(Integer, default=1)
    rcd_sensitivity = Column(Float, nullable=True)    # mA
    note = Column(Text, nullable=True)

    switchboard = relationship("Switchboard", back_populates="devices")
    circuits = relationship("Circuit", back_populates="device", cascade="all, delete-orphan", order_by="Circuit.id")


class Circuit(Base):
    __tablename__ = "circuits"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"), nullable=False)

    room = Column(String(255), nullable=True)
    usage = Column(String(255), nullable=True)           # např. zásuvky, světla, technologie...
    cable_type = Column(String(100), nullable=True)
    cable_size = Column(String(50), nullable=True)
    length = Column(Float, nullable=True)
    outlets_count = Column(Integer, nullable=True)
    note = Column(Text, nullable=True)

    device = relationship("Device", back_populates="circuits")
