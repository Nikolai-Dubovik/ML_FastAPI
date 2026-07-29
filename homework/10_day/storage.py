from datetime import datetime, timezone
from pathlib import Path

import joblib
from sklearn.pipeline import Pipeline

# каталог артефактов models/ — не путать с модулем models.py
MODEL_PATH = Path(__file__).resolve().parent / "models" / "churn_model.joblib"


def save_churn_model(
    pipeline: Pipeline,
    metrics: dict,
    model_type: str,
    hyperparameters: dict,
    path: Path = MODEL_PATH,
) -> dict:
    """Сохраняет bundle (pipeline + конфигурация + время обучения + метрики) и возвращает его."""
    bundle = {
        "pipeline": pipeline,
        "model_type": model_type,
        "hyperparameters": hyperparameters,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, path)
    return bundle


def load_churn_model(path: Path = MODEL_PATH) -> dict | None:
    """Загружает bundle с диска; None, если модель ещё не обучалась."""
    if not path.exists():
        return None
    return joblib.load(path)
