"""Recepción de telemetría y eventos desde el dispositivo (protegido con X-API-Key)."""
from datetime import datetime

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.orm import Session

from ..config import settings
from ..database import get_db
from ..models import Event, TelemetryRecord, Vehicle
from ..schemas import EventIn, TelemetryIn


def check_key(x_api_key: str | None = Header(None)):
    if x_api_key != settings.device_api_key:
        raise HTTPException(401, "API key inválida.")


router = APIRouter(prefix="/api/ingest", tags=["ingesta"], dependencies=[Depends(check_key)])


def _prepare(data, db: Session):
    v = db.query(Vehicle).filter(Vehicle.code == data.vehicle_code).first()
    if not v:
        raise HTTPException(404, f"Vehículo {data.vehicle_code} no registrado.")
    fields = data.model_dump(exclude={"vehicle_code", "received_at"})
    return {"vehicle_id": v.id, **fields}, (data.received_at or datetime.now()).replace(tzinfo=None)


@router.post("/telemetry", status_code=201)
def ingest_telemetry(data: TelemetryIn, db: Session = Depends(get_db)):
    fields, when = _prepare(data, db)
    rec = TelemetryRecord(received_at=when, **fields)
    db.add(rec)
    db.commit()
    return {"id": rec.id}


@router.post("/events", status_code=201)
def ingest_event(data: EventIn, db: Session = Depends(get_db)):
    fields, when = _prepare(data, db)
    ev = Event(occurred_at=when, **fields)
    db.add(ev)
    db.commit()
    return {"id": ev.id}
