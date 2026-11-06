"""Datos de ejemplo: python -m app.seed"""
from datetime import datetime

from .database import Base, SessionLocal, engine
from .models import Classification, Event, TelemetryRecord, User, Vehicle
from .security import hash_password
from .services.classifier import ModelNotAvailable, classifier

FIELDS = ["gross_weight_kg", "speed_kmh", "acceleration_ms2", "speed_before_kmh", "speed_after_kmh",
          "heading_change_deg_s", "road_grade_pct", "altitude_change_m", "event_duration_s", "rpm",
          "can_accelerator_pct", "can_rpm_change_rate", "can_engine_load_pct", "can_brake_switch"]

# (vehículo, fecha, tipo, valores en el orden de FIELDS, tiene CAN, se clasifica al sembrar)
EVENTS = [
    ("CAM-01", datetime(2026, 10, 14, 8, 12), "frenado_brusco", (32000, 62, -2.4, 76, 40, 1.6, 3.0, 1.8, 4, 1232, 7, 285, 61, 1), True, True),
    ("CAM-01", datetime(2026, 10, 14, 15, 40), "giro_brusco", (28000, 41, -0.2, 44, 38, 14.5, 5.2, 3.1, 2, 980, 40, 120, 55, 0), True, True),
    ("CAM-02", datetime(2026, 10, 15, 9, 5), "exceso_velocidad", (18500, 92, 0.3, 90, 93, 0.4, 0.2, 0.5, 12, 1100, 48, 20, 55, 0), True, True),
    ("CAM-02", datetime(2026, 10, 16, 11, 30), "aceleracion_brusca", (30000, 35, 2.8, 18, 52, 2.8, 7.5, 6.0, 5, 660, 66, 16, 69, 0), True, False),
    ("CAM-03", datetime(2026, 10, 16, 17, 22), "frenado_brusco", (15000, 55, -2.6, 66, 40, 0.6, 1.0, 0.5, 3, 1100, 0, 250, 10, 1), True, True),
    ("CAM-01", datetime(2026, 10, 17, 7, 48), "giro_brusco", (31000, 47, 0.2, 49, 45, 11.8, 0.5, 0.3, 3.6, 1700, None, None, None, None), False, False),
]


def run():
    Base.metadata.create_all(engine)
    classifier.load()
    db = SessionLocal()
    if db.query(User).first():
        print("Ya existen datos; no se vuelve a sembrar.")
        return
    db.add(User(email="analista@empresa.com", password_hash=hash_password("analista123")))
    vehicles = {c: Vehicle(code=c, plate=p, imei=i) for c, p, i in [
        ("CAM-01", "ABC-123", "352099001761481"), ("CAM-02", "DEF-456", "352099001761482"),
        ("CAM-03", "GHI-789", "352099001761483")]}
    db.add_all(vehicles.values())
    db.flush()
    for code, when, lat, lon, speed, rpm in [
        ("CAM-01", datetime(2026, 10, 17, 7, 50), -16.4231, -71.5412, 44, 1650),
        ("CAM-02", datetime(2026, 10, 16, 11, 40), -16.3988, -71.5350, 38, 1400),
        ("CAM-03", datetime(2026, 10, 16, 17, 30), -16.4090, -71.5250, 51, 1500)]:
        db.add(TelemetryRecord(vehicle_id=vehicles[code].id, received_at=when, speed_kmh=speed, rpm=rpm,
                               engine_on=True, latitude=lat, longitude=lon))
    events = []
    for code, when, tipo, vals, has_can, classify in EVENTS:
        ev = Event(vehicle_id=vehicles[code].id, occurred_at=when, event_type=tipo, engine_on=True,
                   latitude=-16.41 if has_can else None, longitude=-71.53 if has_can else None,
                   **dict(zip(FIELDS, vals)))
        db.add(ev)
        events.append((ev, classify))
    db.commit()
    try:  # los eventos "procesados" se clasifican con el modelo real
        for ev, classify in events:
            if classify:
                sev, prob, ver = classifier.predict(ev)
                db.add(Classification(event_id=ev.id, severity=sev, probability=prob, model_version=ver))
        db.commit()
    except ModelNotAvailable:
        print("Aviso: no hay modelo en ml/models/; todos los eventos quedan Pendientes (clasifícalos desde la web).")
    print("Datos de ejemplo creados. Usuario: analista@empresa.com / analista123")


if __name__ == "__main__":
    run()