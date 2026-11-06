from datetime import datetime

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .database import Base

EVENT_TYPES = {
    "giro_brusco": "Giro brusco",
    "frenado_brusco": "Frenado brusco",
    "aceleracion_brusca": "Aceleración brusca",
    "exceso_velocidad": "Exceso de velocidad",
}
SEVERITIES = ["Leve", "Moderado", "Grave"]


def num():
    return mapped_column(Float, nullable=True)


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(30), default="analista_flota")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)


class Vehicle(Base):
    __tablename__ = "vehicles"
    id: Mapped[int] = mapped_column(primary_key=True)
    code: Mapped[str] = mapped_column(String(20), unique=True)
    plate: Mapped[str] = mapped_column(String(20))
    imei: Mapped[str] = mapped_column(String(20))
    status: Mapped[str] = mapped_column(String(20), default="Activo")


class TelemetryRecord(Base):
    __tablename__ = "telemetry_records"
    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), index=True)
    received_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    speed_kmh: Mapped[float | None] = num()
    rpm: Mapped[float | None] = num()
    engine_on: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    latitude: Mapped[float | None] = num()
    longitude: Mapped[float | None] = num()


class Event(Base):
    """Evento detectado. Guarda una 'foto' del contexto en el momento de la detección."""

    __tablename__ = "events"
    id: Mapped[int] = mapped_column(primary_key=True)
    vehicle_id: Mapped[int] = mapped_column(ForeignKey("vehicles.id"), index=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    event_type: Mapped[str] = mapped_column(String(30), index=True)
    # contexto básico (telemetría)
    speed_kmh: Mapped[float | None] = num()
    rpm: Mapped[float | None] = num()
    engine_on: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    latitude: Mapped[float | None] = num()
    longitude: Mapped[float | None] = num()
    # variables usadas por el modelo
    gross_weight_kg: Mapped[float | None] = num()
    acceleration_ms2: Mapped[float | None] = num()
    speed_before_kmh: Mapped[float | None] = num()
    speed_after_kmh: Mapped[float | None] = num()
    heading_change_deg_s: Mapped[float | None] = num()
    road_grade_pct: Mapped[float | None] = num()
    altitude_change_m: Mapped[float | None] = num()
    event_duration_s: Mapped[float | None] = num()
    # datos CAN-Bus (opcionales)
    can_accelerator_pct: Mapped[float | None] = num()
    can_engine_load_pct: Mapped[float | None] = num()
    can_rpm_change_rate: Mapped[float | None] = num()
    can_brake_switch: Mapped[float | None] = num()

    vehicle: Mapped["Vehicle"] = relationship()
    classification: Mapped["Classification | None"] = relationship(back_populates="event", uselist=False)

    @property
    def vehicle_code(self): return self.vehicle.code
    @property
    def vehicle_plate(self): return self.vehicle.plate
    @property
    def event_type_label(self): return EVENT_TYPES.get(self.event_type, self.event_type)
    @property
    def status(self): return "Procesado" if self.classification else "Pendiente"
    @property
    def severity(self): return self.classification.severity if self.classification else None
    @property
    def probability(self): return self.classification.probability if self.classification else None
    @property
    def model_version(self): return self.classification.model_version if self.classification else None
    @property
    def classified_at(self): return self.classification.classified_at if self.classification else None
    @property
    def can_available(self):
        return any(v is not None for v in (self.can_accelerator_pct, self.can_engine_load_pct,
                                           self.can_rpm_change_rate, self.can_brake_switch))


class Classification(Base):
    __tablename__ = "classifications"
    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), unique=True)
    severity: Mapped[str] = mapped_column(String(20), index=True)
    probability: Mapped[float | None] = num()
    model_version: Mapped[str] = mapped_column(String(30))
    classified_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    event: Mapped["Event"] = relationship(back_populates="classification")
