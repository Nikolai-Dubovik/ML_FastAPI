import logging

from fastapi import APIRouter

from app import state
from app.errors import ApiError, error_example
from app.ml.history import append_record, load_history
from app.ml.model import predict_churn, train_churn_model
from app.ml.preprocessing import feature_schema, split_info
from app.ml.storage import save_churn_model
from app.schemas import FeatureVectorChurn, PredictionResponseChurn, TrainingConfigChurn

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/")
def get_message():
    return {"message": "ml churn service is running"}


@router.get("/health")
def health():
    return {
        "status": "ok",
        "model_available": state.model_state is not None,
        "dataset_loaded": not state.dataset.df.empty,
    }


@router.post("/predict", responses={
    409: error_example("model_not_trained", "модель ещё не обучена — вызовите POST /model/train"),
    422: error_example("validation_error", "некорректные входные данные"),
})
def predict(
    features: FeatureVectorChurn | list[FeatureVectorChurn],
) -> PredictionResponseChurn | list[PredictionResponseChurn]:
    if state.model_state is None:
        raise ApiError(
            409, "model_not_trained", "модель ещё не обучена — вызовите POST /model/train"
        )
    is_single = isinstance(features, FeatureVectorChurn)
    batch = [features] if is_single else features
    logger.info("предсказание для %s клиентов", len(batch))
    responses = predict_churn(state.model_state["pipeline"], batch)
    return responses[0] if is_single else responses


@router.get("/dataset/preview")
def dataset_preview(n: int = 5):
    return state.dataset.preview(n)


@router.get("/dataset/info")
def dataset_info():
    return state.dataset.info()


@router.get("/dataset/split-info")
def dataset_split_info(test_size: float = 0.2, random_state: int = 42):
    return split_info(state.dataset.df, test_size=test_size, random_state=random_state)


@router.get("/model/schema")
def model_schema():
    return feature_schema(state.dataset.df)


@router.post("/model/train", responses={
    400: error_example("data_error", "ошибка обработки данных: неизвестный гиперпараметр"),
    422: error_example("validation_error", "некорректные входные данные"),
})
def model_train(config: TrainingConfigChurn = TrainingConfigChurn()):
    if state.dataset.df.empty:
        raise ApiError(400, "empty_dataset", "датасет не загружен или пуст")
    # ошибки sklearn (например, несуществующий гиперпараметр) ловит глобальный обработчик
    pipeline, metrics = train_churn_model(
        state.dataset.df, config.model_type, config.hyperparameters
    )
    logger.info("модель обучена: %s, метрики %s", config.model_type, metrics)
    state.model_state = save_churn_model(
        pipeline, metrics, config.model_type, config.hyperparameters
    )
    append_record({
        "trained_at": state.model_state["trained_at"],
        "model_type": config.model_type,
        "hyperparameters": config.hyperparameters,
        "metrics": metrics,
    })
    return {
        "model_type": config.model_type,
        "hyperparameters": config.hyperparameters,
        "metrics": metrics,
    }


@router.get("/model/status")
def model_status():
    if state.model_state is None:
        return {"is_trained": False, "trained_at": None, "metrics": None}
    return {
        "is_trained": True,
        "trained_at": state.model_state["trained_at"],
        "model_type": state.model_state["model_type"],
        "hyperparameters": state.model_state["hyperparameters"],
        "metrics": state.model_state["metrics"],
    }


@router.get("/model/metrics", responses={
    409: error_example("model_not_trained", "модель ещё не обучалась — вызовите POST /model/train"),
})
def model_metrics(limit: int = 5, model_type: str | None = None):
    history = load_history()
    # фильтр раньше среза, иначе отберём только из хвоста
    if model_type:
        history = [record for record in history if record["model_type"] == model_type]
    if not history:
        raise ApiError(
            409, "model_not_trained", "модель ещё не обучалась — вызовите POST /model/train"
        )
    return {"last": history[-1], "history": history[-limit:]}
