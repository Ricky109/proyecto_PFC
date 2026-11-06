import os
import tempfile
from pathlib import Path

# Variables de entorno de prueba: se definen ANTES de importar la aplicación.
_tmp = Path(tempfile.mkdtemp())
os.environ["DATABASE_URL"] = f"sqlite:///{(_tmp / 'test.db').as_posix()}"
os.environ["SECRET_KEY"] = "clave-solo-para-pruebas"
os.environ["DEVICE_API_KEY"] = "clave-dispositivo-pruebas"
os.environ["MODEL_PATH"] = str(_tmp / "no-existe.pkl")
os.environ["ALLOW_DEMO_MODEL"] = "true"  # las pruebas no dependen del modelo real

import pytest
from fastapi.testclient import TestClient

from app import seed
from app.main import app


@pytest.fixture(scope="session")
def client():
    seed.run()  # usuario, vehículos y 6 eventos de ejemplo
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="session")
def auth_headers(client):
    r = client.post("/api/auth/login", json={"email": "analista@empresa.com", "password": "analista123"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}
