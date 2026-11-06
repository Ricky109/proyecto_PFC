from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .database import Base, engine
from .routers import auth, events, ingest, vehicles
from .services.classifier import classifier


@asynccontextmanager
async def lifespan(app: FastAPI):
    Base.metadata.create_all(engine)
    classifier.load()
    yield


app = FastAPI(title="TRANSMIND AI API", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.cors_origins.split(",")],
    allow_methods=["*"],
    allow_headers=["*"],
)
for r in (auth.router, events.router, vehicles.router, ingest.router):
    app.include_router(r)


@app.get("/api/health", tags=["sistema"])
def health():
    return {"status": "ok", "model_loaded": classifier.ready, "model_version": classifier.version}
