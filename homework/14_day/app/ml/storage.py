import logging
from datetime import datetime, timezone
from pathlib import Path

import joblib
from sklearn.pipeline import Pipeline

from app.config import MODEL_PATH

logger = logging.getLogger("churn.storage")


def save_churn_model(
    pipeline: Pipeline,
    metrics: dict,
    model_type: str,
    hyperparameters: dict,
    path: Path | None = None,
) -> dict:
    """Сохраняет bundle (pipeline + конфигурация + время обучения + метрики) и возвращает его."""
    # путь разрешаем в момент вызова, а не при импорте: так его можно подменить в тестах
    path = Path(path or MODEL_PATH)
    bundle = {
        "pipeline": pipeline,
        "model_type": model_type,
        "hyperparameters": hyperparameters,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "metrics": metrics,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(bundle, path)
    logger.info("модель сохранена: %s", path)
    return bundle


def load_churn_model(path: Path | None = None) -> dict | None:
    """Загружает bundle с диска; None, если модель ещё не обучалась."""
    path = Path(path or MODEL_PATH)
    if not path.exists():
        logger.info("обученной модели нет: %s", path)
        return None
    bundle = joblib.load(path)
    logger.info("модель загружена: %s (обучена %s)", path, bundle["trained_at"])
    return bundle
