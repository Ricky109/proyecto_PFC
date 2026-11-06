from app.models import Event
from app.services.classifier import build_row

DEVICE = {"X-API-Key": "clave-dispositivo-pruebas"}


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200 and r.json()["status"] == "ok"


def test_login_correcto_e_incorrecto(client):
    ok = client.post("/api/auth/login", json={"email": "analista@empresa.com", "password": "analista123"})
    assert ok.status_code == 200 and ok.json()["access_token"]
    mal = client.post("/api/auth/login", json={"email": "analista@empresa.com", "password": "otra"})
    assert mal.status_code == 401


def test_eventos_requieren_autenticacion(client):
    assert client.get("/api/events").status_code == 401


def test_resumen_y_filtros(client, auth_headers):
    resumen = client.get("/api/events/summary", headers=auth_headers).json()
    assert resumen["events"] == 6 and resumen["vehicles"] == 3
    pendientes = client.get("/api/events", headers=auth_headers, params={"status": "pendiente"}).json()
    assert all(e["status"] == "Pendiente" for e in pendientes["items"])


def test_rango_de_fechas_invalido(client, auth_headers):
    r = client.get("/api/events", headers=auth_headers, params={"desde": "2026-10-17", "hasta": "2026-10-01"})
    assert r.status_code == 422


def test_clasificar_evento_pendiente_una_sola_vez(client, auth_headers):
    primero = client.post("/api/events/4/classify", headers=auth_headers)
    assert primero.status_code == 200 and primero.json()["status"] == "Procesado"
    segundo = client.post("/api/events/4/classify", headers=auth_headers)
    assert segundo.status_code == 409


def test_detalle_de_vehiculo(client, auth_headers):
    v = client.get("/api/vehicles/1", headers=auth_headers).json()
    assert v["code"] == "CAM-01" and v["last_telemetry"] and v["events"]


def test_ingesta_exige_api_key(client):
    cuerpo = {"vehicle_code": "CAM-02", "event_type": "giro_brusco"}
    assert client.post("/api/ingest/events", json=cuerpo).status_code == 401


def test_ingesta_rechaza_tipo_invalido(client):
    cuerpo = {"vehicle_code": "CAM-02", "event_type": "inventado"}
    assert client.post("/api/ingest/events", json=cuerpo, headers=DEVICE).status_code == 422


def test_ingesta_de_evento_valido(client):
    cuerpo = {"vehicle_code": "CAM-02", "event_type": "giro_brusco", "speed_kmh": 30,
              "acceleration_ms2": 1.0, "gross_weight_kg": 20000}
    assert client.post("/api/ingest/events", json=cuerpo, headers=DEVICE).status_code == 201


def test_variables_del_modelo_one_hot_y_rpm():
    fila = build_row(Event(event_type="giro_brusco", rpm=1000.0))
    assert fila["event_type_giro_brusco"] == 1.0
    assert fila["event_type_frenado_brusco"] == 0.0
    assert fila["can_engine_rpm"] == fila["can_engine_rpm.1"] == 1000.0
