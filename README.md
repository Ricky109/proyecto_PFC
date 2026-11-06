# TRANSMIND AI — Prototipo funcional

Frontend **Vue 3 (Vite)** · Backend **FastAPI** · Base de datos **PostgreSQL** · Modelo de ML (scikit-learn) exportado desde Colab.

```
transmind-ai/
├── frontend/          Vue 3: login, eventos (+historial), detalle/clasificación, vehículo
├── backend/app/       FastAPI: auth, events, vehicles, ingest, services/classifier.py
├── ml/models/         aquí va model.joblib (exportado desde Colab)
└── docker-compose.yml PostgreSQL
```

## 1. Exportar el modelo desde Colab
En la misma sesión donde entrenaste (usa tu variable `model` y el `X_train` con el que entrenaste):

```python
import joblib, sklearn
print(sklearn.__version__)           # <- instala esta misma versión en el backend
paquete = {
    "model": model,
    "features": list(X_train.columns),   # orden exacto de columnas del entrenamiento
    "version": "v1.0",
    # "label_map": {0: "Leve", 1: "Moderado", 2: "Grave"},  # solo si las clases son numéricas
}
joblib.dump(paquete, "model.joblib")
from google.colab import files; files.download("model.joblib")
```
Copia el archivo a `ml/models/model.joblib`.

## 2. Base de datos
```bash
docker compose up -d
```
(Sin Docker: crea una BD PostgreSQL y ajusta `DATABASE_URL` en `backend/.env`; o para probar rápido usa `DATABASE_URL=sqlite:///./transmind.db`.)

## 3. Backend
```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
pip install scikit-learn==X.Y.Z    # la versión impresa en Colab
python -m app.seed                 # crea tablas, usuario, vehículos y eventos de ejemplo
uvicorn app.main:app --reload --port 8000
```
Comprobar: http://localhost:8000/api/health (`model_loaded: true`) · documentación: http://localhost:8000/docs

## 4. Frontend
```bash
cd frontend
npm install
npm run dev
```
Abrir http://localhost:5173 — usuario `analista@empresa.com`, contraseña `analista123`.

## Notas
- Sin `model.joblib`, el sistema funciona pero "Clasificar evento" responde que el modelo no está disponible. Para probar solo la interfaz: `ALLOW_DEMO_MODEL=true` en `backend/.env` (usa una regla simple, no el modelo real).
- `seed` clasifica con el modelo real los eventos de ejemplo marcados como procesados; si no hay modelo quedan todos pendientes.
- Variables del modelo → `backend/app/services/classifier.py` (`build_row`). Gravedad numérica → `LABELS_BY_INDEX` o `label_map`.
- Variables de contexto mostradas en el detalle → `frontend/src/contextVariables.js`.
- Recepción de dispositivo: `POST /api/ingest/telemetry` y `POST /api/ingest/events` con cabecera `X-API-Key` (valor en `DEVICE_API_KEY`).
