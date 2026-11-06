"""Carga el modelo exportado desde Colab y clasifica la gravedad de un evento."""
import json
import logging
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from ..config import ROOT, settings
from ..models import EVENT_TYPES

log = logging.getLogger("transmind.classifier")

# Variables del entrenamiento (gráfica de importancia). Si el archivo exportado trae
# "features" o el modelo tiene feature_names_in_, se usa ese orden en lugar de esta lista.
DEFAULT_FEATURES = [
    "gross_weight_kg", "speed", "acceleration_ms2", "speed_after_kmh", "heading_change_deg_s",
    "speed_before_kmh", "event_type_giro_brusco", "road_grade_pct", "can_accelerator_pct",
    "event_type_aceleracion_brusca", "altitude_change_m", "event_type_frenado_brusco",
    "can_engine_rpm", "can_rpm_change_rate", "can_engine_rpm.1", "can_engine_load_pct",
    "can_brake_switch", "event_duration_s",
]

LABELS = {
    "leve": "Leve", "bajo": "Leve", "low": "Leve",
    "moderado": "Moderado", "medio": "Moderado", "medium": "Moderado", "moderate": "Moderado",
    "grave": "Grave", "alto": "Grave", "high": "Grave", "severe": "Grave",
    "justificado": "Justificado",
}
LABELS_BY_INDEX = {0: "Leve", 1: "Moderado", 2: "Grave"}  # solo si NO hay label_encoder
DEFAULT_CLASSES = ["Justificado", "Leve", "Moderado", "Grave"]  # si no hay modelo cargado
CLASS_ORDER = ["Justificado", "Leve", "Moderado", "Grave"]


class ModelNotAvailable(Exception):
    pass


def _num(v):
    return np.nan if v is None else float(v)


def build_row(ev) -> dict:
    """Convierte un evento de la BD en las variables que espera el modelo."""
    row = {
        "gross_weight_kg": _num(ev.gross_weight_kg),
        "speed": _num(ev.speed_kmh),
        "acceleration_ms2": _num(ev.acceleration_ms2),
        "speed_before_kmh": _num(ev.speed_before_kmh),
        "speed_after_kmh": _num(ev.speed_after_kmh),
        "heading_change_deg_s": _num(ev.heading_change_deg_s),
        "road_grade_pct": _num(ev.road_grade_pct),
        "altitude_change_m": _num(ev.altitude_change_m),
        "event_duration_s": _num(ev.event_duration_s),
        "can_accelerator_pct": _num(ev.can_accelerator_pct),
        "can_engine_rpm": _num(ev.rpm),
        "can_engine_rpm.1": _num(ev.rpm),  # columna duplicada en el dataset original
        "can_rpm_change_rate": _num(ev.can_rpm_change_rate),
        "can_engine_load_pct": _num(ev.can_engine_load_pct),
        "can_brake_switch": _num(ev.can_brake_switch),
    }
    for slug in EVENT_TYPES:  # one-hot del tipo de evento
        row[f"event_type_{slug}"] = 1.0 if ev.event_type == slug else 0.0
    row["event_type_exceso_de_velocidad"] = row["event_type_exceso_velocidad"]
    return row


class Classifier:
    def __init__(self):
        self.model = None
        self.features = DEFAULT_FEATURES
        self.version = settings.model_version
        self.label_map: dict = {}
        self.encoder = None
        self.demo = False

    @property
    def ready(self) -> bool:
        return self.model is not None or self.demo

    @staticmethod
    def _resolve(p: str) -> Path:
        path = Path(p)
        return path if path.is_absolute() else (ROOT / path).resolve()

    def load(self):
        path = self._resolve(settings.model_path)
        if not path.exists():
            if settings.allow_demo_model:
                self.demo, self.version = True, "demo"
                log.warning("Modelo no encontrado en %s: usando MODELO DEMO (solo para pruebas).", path)
            else:
                log.warning("Modelo no encontrado en %s. La clasificación no estará disponible.", path)
            return
        try:
            obj = joblib.load(path)  # lee también .pkl generados con pickle
            if isinstance(obj, dict):  # paquete: {"model", "features", "version", "label_map"}
                self.model = obj["model"]
                self.version = obj.get("version", self.version)
                self.label_map = obj.get("label_map") or {}
                feats = obj.get("features")
            else:
                self.model, feats = obj, None
            enc_path = self._resolve(settings.label_encoder_path)
            if enc_path.exists():
                self.encoder = joblib.load(enc_path)
            feat_path = self._resolve(settings.features_path)
            if feats is None and feat_path.exists():
                feats = json.loads(feat_path.read_text(encoding="utf-8"))
            self.features = list(feats or getattr(self.model, "feature_names_in_", DEFAULT_FEATURES))
            if not feats and not hasattr(self.model, "feature_names_in_"):
                log.warning("El modelo no guarda los nombres de variables: se usa DEFAULT_FEATURES; "
                            "verifica que el orden coincida con el del entrenamiento (features.json).")
            log.info("Modelo cargado con %d variables (label encoder: %s).", len(self.features),
                     "sí" if self.encoder is not None else "no")
        except Exception:
            log.exception("No se pudo cargar el modelo (¿versión de scikit-learn o librería faltante?)")
            self.model = None

    def _label(self, c) -> str:
        if self.encoder is not None and isinstance(c, (int, np.integer)):
            c = self.encoder.inverse_transform([int(c)])[0]  # código numérico -> texto original
        if c in self.label_map:
            return self.label_map[c]
        s = str(c).strip().lower()
        if s in LABELS:
            return LABELS[s]
        if s.lstrip("-").isdigit():
            return LABELS_BY_INDEX.get(int(s), str(c))
        return str(c).strip().capitalize()

    def classes(self) -> list[str]:
        """Categorías de gravedad que maneja el modelo (para los filtros de la interfaz)."""
        if self.encoder is not None:
            raw = list(self.encoder.classes_)
        elif self.model is not None and hasattr(self.model, "classes_"):
            raw = list(self.model.classes_)
        else:
            return DEFAULT_CLASSES
        labels = {self._label(c) for c in raw}
        return sorted(labels, key=lambda x: CLASS_ORDER.index(x) if x in CLASS_ORDER else 99)

    def _demo(self, ev):
        score = abs(ev.acceleration_ms2 or 0) * (1 + (ev.gross_weight_kg or 0) / 40000) + (ev.speed_kmh or 0) / 40
        return ("Grave" if score >= 7 else "Moderado" if score >= 4 else "Leve"), None, self.version

    def predict(self, ev):
        """Devuelve (gravedad, probabilidad | None, versión del modelo)."""
        if self.demo:
            return self._demo(ev)
        if self.model is None:
            raise ModelNotAvailable()
        row = build_row(ev)
        absent = [f for f in self.features if f not in row]
        if absent:
            log.warning("Variables del modelo sin equivalente (se envían como NaN): %s", absent)
        X = pd.DataFrame([[row.get(f, np.nan) for f in self.features]], columns=self.features)
        if not hasattr(self.model, "predict_proba"):
            return self._label(self.model.predict(X)[0]), None, self.version
        try:
            p = self.model.predict_proba(X)[0]
        except ValueError:  # el modelo no admite NaN (p. ej. sin datos CAN)
            p = self.model.predict_proba(X.fillna(0.0))[0]
        i = int(np.argmax(p))
        return self._label(self.model.classes_[i]), float(p[i]), self.version


classifier = Classifier()