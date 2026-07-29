"""Все эндпоинты churn-сервиса."""

import logging

from fastapi import APIRouter

from app.errors import (
    ERROR_RESPONSES,
    EmptyDatasetError,
    ModelNotTrainedError,
    TrainingError,
)
from app.ml.dataset import ChurnDataset
from app.ml.history import append_record, load_history
from app.ml.model import predict_churn, train_churn_model
from app.ml.preprocessing import feature_schema, split_info
from app.ml.storage import load_churn_model, save_churn_model
from app.schemas import (
    FeatureVectorChurn,
    PredictionResponseChurn,
    TrainingConfigChurn,
)

logger = logging.getLogger("churn.api")

router = APIRouter()

# датасет загружается один раз при старте приложения
dataset = ChurnDataset()

# bundle модели (pipeline + конфигурация + время обучения + метрики), если она уже обучалась
model_state: dict | None = load_churn_model()


@router.get("/")
def get_message():
    return {"message": "ml churn service is running"}


@router.get("/health")
def health():
    """Состояние сервиса для healthcheck'ов: есть ли датасет и обученная модель."""
    dataset_loaded = dataset.df is not None and not dataset.df.empty
    model_available = model_state is not None
    return {
        "status": "ok" if (dataset_loaded and model_available) else "degraded",
        "model_available": model_available,
        "dataset_loaded": dataset_loaded,
    }


@router.post("/predict", responses={409: ERROR_RESPONSES[409], 422: ERROR_RESPONSES[422]})
def predict(
    features: FeatureVectorChurn | list[FeatureVectorChurn],
) -> PredictionResponseChurn | list[PredictionResponseChurn]:
    if model_state is None:
        raise ModelNotTrainedError("модель ещё не обучена — вызовите POST /model/train")
    is_single = isinstance(features, FeatureVectorChurn)
    batch = [features] if is_single else features
    responses = predict_churn(model_state["pipeline"], batch)
    # логируем факт события, а не payload с данными клиента
    logger.info("predict: %d объект(ов) → %s", len(batch), [r.prediction for r in responses])
    return responses[0] if is_single else responses


@router.get("/dataset/preview")
def dataset_preview(n: int = 5):
    return dataset.preview(n)


@router.get("/dataset/info")
def dataset_info():
    return dataset.info()


@router.get("/dataset/split-info")
def dataset_split_info(test_size: float = 0.2, random_state: int = 42):
    return split_info(dataset.df, test_size=test_size, random_state=random_state)


@router.get("/model/schema")
def model_schema():
    return feature_schema(dataset.df)


@router.post("/model/train", responses={400: ERROR_RESPONSES[400], 422: ERROR_RESPONSES[422]})
def model_train(config: TrainingConfigChurn = TrainingConfigChurn()):
    global model_state
    if dataset.df is None or dataset.df.empty:
        raise EmptyDatasetError("датасет не загружен или пуст")
    try:
        pipeline, metrics = train_churn_model(
            dataset.df, config.model_type, config.hyperparameters
        )
    except (TypeError, ValueError) as exc:
        # sklearn кидает TypeError на несуществующий гиперпараметр
        raise TrainingError("не удалось обучить модель", {"reason": str(exc)})
    model_state = save_churn_model(
        pipeline, metrics, config.model_type, config.hyperparameters
    )
    append_record({
        # timestamp берём из bundle — одно и то же время обучения в модели и в истории
        "timestamp": model_state["trained_at"],
        "model_type": config.model_type,
        "hyperparameters": config.hyperparameters,
        "metrics": metrics,
    })
    logger.info(
        "обучение %s: accuracy=%s f1=%s roc_auc=%s",
        config.model_type, metrics["accuracy"], metrics["f1"], metrics["roc_auc"],
    )
    return {
        "model_type": config.model_type,
        "hyperparameters": config.hyperparameters,
        "metrics": metrics,
    }


@router.get("/model/metrics")
def model_metrics(model_type: str | None = None, limit: int = 5):
    """Метрики последнего обучения и несколько последних записей истории."""
    history = load_history()
    if model_type:
        history = [record for record in history if record["model_type"] == model_type]
    return {"last": history[-1] if history else None, "history": history[-limit:]}


@router.get("/model/status")
def model_status():
    if model_state is None:
        return {"is_trained": False, "trained_at": None, "metrics": None}
    return {
        "is_trained": True,
        "trained_at": model_state["trained_at"],
        "model_type": model_state.get("model_type"),
        "hyperparameters": model_state.get("hyperparameters"),
        "metrics": model_state["metrics"],
    }
