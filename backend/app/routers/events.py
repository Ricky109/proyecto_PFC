import logging
from datetime import date, datetime, time

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from ..database import get_db
from ..models import EVENT_TYPES, Classification, Event
from ..schemas import EventDetail, Page, Summary
from ..security import get_current_user
from ..services.classifier import ModelNotAvailable, classifier

log = logging.getLogger("transmind.events")
router = APIRouter(prefix="/api", tags=["eventos"], dependencies=[Depends(get_current_user)])


class Filters:
    def __init__(self, desde: date | None = None, hasta: date | None = None, vehicle_id: int | None = None,
                 event_type: str | None = None, severity: str | None = None, status: str | None = None):
        if desde and hasta and desde > hasta:
            raise HTTPException(422, "La fecha inicial debe ser menor o igual a la final.")
        if event_type and event_type not in EVENT_TYPES:
            raise HTTPException(422, "Tipo de evento no válido.")
        if status and status not in ("pendiente", "procesado"):
            raise HTTPException(422, "Estado no válido.")
        self.desde, self.hasta, self.vehicle_id = desde, hasta, vehicle_id
        self.event_type, self.severity, self.status = event_type, severity, status


def build_query(db: Session, f: Filters, only_classified: bool = False):
    q = db.query(Event).outerjoin(Classification, Classification.event_id == Event.id)
    if f.desde:
        q = q.filter(Event.occurred_at >= datetime.combine(f.desde, time.min))
    if f.hasta:
        q = q.filter(Event.occurred_at <= datetime.combine(f.hasta, time.max))
    if f.vehicle_id:
        q = q.filter(Event.vehicle_id == f.vehicle_id)
    if f.event_type:
        q = q.filter(Event.event_type == f.event_type)
    if f.severity:
        q = q.filter(Classification.severity == f.severity)
    if only_classified or f.status == "procesado":
        q = q.filter(Classification.id.is_not(None))
    elif f.status == "pendiente":
        q = q.filter(Classification.id.is_(None))
    return q


def paginate(q, order, page: int, page_size: int) -> dict:
    total = q.with_entities(func.count(Event.id)).scalar()
    rows = (q.options(selectinload(Event.vehicle), selectinload(Event.classification))
            .order_by(order).offset((page - 1) * page_size).limit(page_size).all())
    return {"items": rows, "total": total, "page": page, "page_size": page_size}


@router.get("/severities", response_model=list[str])
def severities():
    return classifier.classes()


@router.get("/events/summary", response_model=Summary)
def summary(f: Filters = Depends(), db: Session = Depends(get_db)):
    q = build_query(db, f)
    count = lambda qq: qq.with_entities(func.count(Event.id)).scalar()
    return Summary(
        events=count(q),
        pending=count(q.filter(Classification.id.is_(None))),
        severe=count(q.filter(Classification.severity == "Grave")),
        vehicles=q.with_entities(func.count(func.distinct(Event.vehicle_id))).scalar(),
    )


@router.get("/events", response_model=Page)
def list_events(f: Filters = Depends(), page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=50),
                db: Session = Depends(get_db)):
    return paginate(build_query(db, f), Event.occurred_at.desc(), page, page_size)


@router.get("/classifications", response_model=Page)
def history(f: Filters = Depends(), page: int = Query(1, ge=1), page_size: int = Query(10, ge=1, le=50),
            db: Session = Depends(get_db)):
    return paginate(build_query(db, f, only_classified=True), Classification.classified_at.desc(), page, page_size)


def get_or_404(db: Session, event_id: int) -> Event:
    ev = db.get(Event, event_id)
    if not ev:
        raise HTTPException(404, "Evento no encontrado.")
    return ev


@router.get("/events/{event_id}", response_model=EventDetail)
def event_detail(event_id: int, db: Session = Depends(get_db)):
    return get_or_404(db, event_id)


@router.post("/events/{event_id}/classify", response_model=EventDetail)
def classify(event_id: int, db: Session = Depends(get_db)):
    ev = get_or_404(db, event_id)
    if ev.classification:
        raise HTTPException(409, "El evento ya fue clasificado.")
    if any(getattr(ev, n) is None for n in ("speed_kmh", "acceleration_ms2", "gross_weight_kg")):
        raise HTTPException(422, "Faltan datos del evento (velocidad, aceleración o peso) para clasificarlo.")
    try:
        severity, prob, version = classifier.predict(ev)
    except ModelNotAvailable:
        raise HTTPException(503, "El modelo de clasificación no está disponible.")
    except Exception:
        log.exception("Error del modelo al clasificar el evento %s", event_id)
        raise HTTPException(500, "Error del modelo al clasificar el evento.")
    db.add(Classification(event_id=ev.id, severity=severity, probability=prob, model_version=version))
    db.commit()
    db.refresh(ev)
    return ev