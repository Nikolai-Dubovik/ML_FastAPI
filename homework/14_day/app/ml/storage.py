from datetime import datetime, timezone

import joblib
from sklearn.pipeline import Pipeline

from app import config


def save_churn_model(
    pipeline: Pipeline,
    metrics: dict,
    model_type: str,
    hyperparameters: dict,
) -> dict:
    """Сохраняет bundle (pipeline + конфигурация + время обучения + метрики) и возвращает его."""
    bundle = {
        "pipeline": pipeline,
        "model_type": model_type,
        "hyperparameters": hyperparameters,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
    }
    config.MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, config.MODEL_PATH)
    return bundle


def load_churn_model() -> dict | None:
    """Загружает bundle с диска; None, если модель ещё не обучалась."""
    if not config.MODEL_PATH.exists():
        return None
    return joblib.load(config.MODEL_PATH)
