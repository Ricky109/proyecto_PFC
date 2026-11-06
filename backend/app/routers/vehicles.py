from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..models import Event, TelemetryRecord, Vehicle
from ..schemas import VehicleDetail, VehicleOut
from ..security import get_current_user

router = APIRouter(prefix="/api/vehicles", tags=["vehículos"], dependencies=[Depends(get_current_user)])


@router.get("", response_model=list[VehicleOut])
def list_vehicles(db: Session = Depends(get_db)):
    return db.query(Vehicle).order_by(Vehicle.code).all()


@router.get("/{vehicle_id}", response_model=VehicleDetail)
def vehicle_detail(vehicle_id: int, db: Session = Depends(get_db)):
    v = db.get(Vehicle, vehicle_id)
    if not v:
        raise HTTPException(404, "Vehículo no encontrado.")
    last = (db.query(TelemetryRecord).filter(TelemetryRecord.vehicle_id == v.id)
            .order_by(TelemetryRecord.received_at.desc()).first())
    events = (db.query(Event).filter(Event.vehicle_id == v.id)
              .options(selectinload(Event.vehicle), selectinload(Event.classification))
              .order_by(Event.occurred_at.desc()).all())
    return {"id": v.id, "code": v.code, "plate": v.plate, "imei": v.imei, "status": v.status,
            "last_telemetry": last, "events": events}
