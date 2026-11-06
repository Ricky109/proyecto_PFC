from datetime import datetime

from pydantic import BaseModel, ConfigDict, field_validator

from .models import EVENT_TYPES


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LoginIn(BaseModel):
    email: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    email: str
    role: str


class EventOut(ORM):
    id: int
    occurred_at: datetime
    vehicle_id: int
    vehicle_code: str
    vehicle_plate: str
    event_type: str
    event_type_label: str
    status: str
    severity: str | None
    probability: float | None
    model_version: str | None
    classified_at: datetime | None


class EventDetail(EventOut):
    speed_kmh: float | None
    rpm: float | None
    engine_on: bool | None
    latitude: float | None
    longitude: float | None
    can_available: bool
    gross_weight_kg: float | None
    acceleration_ms2: float | None
    speed_before_kmh: float | None
    speed_after_kmh: float | None
    heading_change_deg_s: float | None
    road_grade_pct: float | None
    altitude_change_m: float | None
    event_duration_s: float | None


class Page(BaseModel):
    items: list[EventOut]
    total: int
    page: int
    page_size: int


class Summary(BaseModel):
    events: int
    pending: int
    severe: int
    vehicles: int


class VehicleOut(ORM):
    id: int
    code: str
    plate: str
    imei: str
    status: str


class TelemetryOut(ORM):
    received_at: datetime
    speed_kmh: float | None
    rpm: float | None
    engine_on: bool | None
    latitude: float | None
    longitude: float | None


class VehicleDetail(VehicleOut):
    last_telemetry: TelemetryOut | None
    events: list[EventOut]


# ---- Ingesta desde el dispositivo telemático ----
class TelemetryIn(BaseModel):
    vehicle_code: str
    received_at: datetime | None = None
    speed_kmh: float | None = None
    rpm: float | None = None
    engine_on: bool | None = None
    latitude: float | None = None
    longitude: float | None = None


class EventIn(TelemetryIn):
    event_type: str
    gross_weight_kg: float | None = None
    acceleration_ms2: float | None = None
    speed_before_kmh: float | None = None
    speed_after_kmh: float | None = None
    heading_change_deg_s: float | None = None
    road_grade_pct: float | None = None
    altitude_change_m: float | None = None
    event_duration_s: float | None = None
    can_accelerator_pct: float | None = None
    can_engine_load_pct: float | None = None
    can_rpm_change_rate: float | None = None
    can_brake_switch: float | None = None

    @field_validator("event_type")
    @classmethod
    def valid_type(cls, v):
        if v not in EVENT_TYPES:
            raise ValueError(f"event_type debe ser uno de: {', '.join(EVENT_TYPES)}")
        return v
