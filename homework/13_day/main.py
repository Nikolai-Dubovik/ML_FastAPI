import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from dataset import ChurnDataset
from errors import ChurnError, EmptyDatasetError, ModelNotTrainedError, TrainingError
from history import append_record, load_history
from logging_config import setup_logging
from model import predict_churn, train_churn_model
from models import (
    ErrorResponse,
    FeatureVectorChurn,
    PredictionResponseChurn,
    TrainingConfigChurn,
)
from preprocessing import feature_schema, split_info
from storage import load_churn_model, save_churn_model

# настраиваем логи до создания приложения — чтобы события старта тоже попали в лог
setup_logging()
logger = logging.getLogger("churn.main")

app = FastAPI(title="ML Churn Service")

# датасет загружается один раз при старте приложения
dataset = ChurnDataset()

# модель (bundle: pipeline + trained_at + metrics) загружается при старте, если уже обучалась
model_state: dict | None = load_churn_model()

# описания ошибок для /docs
ERROR_RESPONSES = {
    400: {"model": ErrorResponse, "description": "пустой датасет или ошибка обучения"},
    409: {"model": ErrorResponse, "description": "модель ещё не обучена"},
    422: {"model": ErrorResponse, "description": "ошибка валидации входных данных"},
}


def error_response(status_code: int, code: str, message: str, details=None) -> JSONResponse:
    """Единый формат тела ошибки для всех обработчиков."""
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "details": details}},
    )


@app.exception_handler(ChurnError)
def handle_churn_error(request: Request, exc: ChurnError) -> JSONResponse:
    """Наши доменные ошибки: статус и код берём из самого исключения."""
    logger.warning("%s %s → %s: %s", request.method, request.url.path, exc.code, exc.message)
    return error_response(exc.status_code, exc.code, exc.message, exc.details)


# /predict принимает union (один объект или список), и pydantic вставляет в loc
# имя варианта — клиенту оно не нужно
UNION_BRANCHES = {"FeatureVectorChurn", "list[FeatureVectorChurn]"}


def validation_errors(exc: RequestValidationError) -> list[dict]:
    """Разворачивает ошибки pydantic в компактный список field / type / message."""
    errors = []
    for err in exc.errors():
        # loc = ("body", "monthly_fee") или ("body", "FeatureVectorChurn", "monthly_fee")
        parts = [str(part) for part in err["loc"][1:] if str(part) not in UNION_BRANCHES]
        if not parts:
            # ошибка от неподошедшего варианта union («это не список») — шум, поле не указано
            continue
        errors.append({
            "field": ".".join(parts),
            "type": err["type"],
            "message": err["msg"],
        })
    # тело целиком не то (например, прислали строку) — конкретных полей нет
    if not errors:
        errors = [
            {"field": "body", "type": err["type"], "message": err["msg"]}
            for err in exc.errors()
        ]
    return errors


@app.exception_handler(RequestValidationError)
def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Ошибки Pydantic: неверные типы значений и нехватка признаков."""
    errors = validation_errors(exc)
    logger.warning(
        "%s %s → validation_error: %s",
        request.method, request.url.path, [err["field"] for err in errors],
    )
    return error_response(
        422, "validation_error", "ошибка валидации входных данных", {"errors": errors}
    )


@app.exception_handler(StarletteHTTPException)
def handle_http_error(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """Ошибки самого фреймворка (404 на неизвестный путь, 405) — в том же формате."""
    return error_response(exc.status_code, "http_error", str(exc.detail))


@app.exception_handler(Exception)
def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    """Всё непредвиденное: клиенту — общий текст, трассировка наружу не уходит."""
    # logger.exception пишет трассировку в лог — там она нужна, в ответе нет
    logger.exception("%s %s → internal_error", request.method, request.url.path)
    return error_response(500, "internal_error", "внутренняя ошибка сервиса")


@app.get("/")
def get_message():
    return {"message": "ml churn service is running"}


@app.get("/health")
def health():
    """Состояние сервиса для healthcheck'ов: есть ли датасет и обученная модель."""
    dataset_loaded = dataset.df is not None and not dataset.df.empty
    model_available = model_state is not None
    return {
        "status": "ok" if (dataset_loaded and model_available) else "degraded",
        "model_available": model_available,
        "dataset_loaded": dataset_loaded,
    }


@app.post("/predict", responses={409: ERROR_RESPONSES[409], 422: ERROR_RESPONSES[422]})
def predict(
    features: FeatureVectorChurn | list[FeatureVectorChurn],
) -> PredictionResponseChurn | list[PredictionResponseChurn]:
    if model_state is None:
        raise ModelNotTrainedError("модель ещё не обучена — вызовите POST /model/train")
    is_single = isinstance(features, FeatureVectorChurn)
    batch = [features] if is_single else features
    responses = predict_churn(model_state["pipeline"], batch)
    # логируем факт события, а не сам payload с данными клиента
    logger.info(
        "predict: %d объект(ов) → %s", len(batch), [r.prediction for r in responses]
    )
    return responses[0] if is_single else responses


@app.get("/dataset/preview")
def dataset_preview(n: int = 5):
    return dataset.preview(n)


@app.get("/dataset/info")
def dataset_info():
    return dataset.info()


@app.get("/dataset/split-info")
def dataset_split_info(test_size: float = 0.2, random_state: int = 42):
    return split_info(dataset.df, test_size=test_size, random_state=random_state)


@app.get("/model/schema")
def model_schema():
    return feature_schema(dataset.df)


@app.post("/model/train", responses={400: ERROR_RESPONSES[400], 422: ERROR_RESPONSES[422]})
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


@app.get("/model/metrics")
def model_metrics(model_type: str | None = None, limit: int = 5):
    """Метрики последнего обучения и несколько последних записей истории."""
    history = load_history()
    if model_type:
        history = [record for record in history if record["model_type"] == model_type]
    return {
        "last": history[-1] if history else None,
        # limit последних записей: срез хвоста, чтобы сравнить свежие прогоны
        "history": history[-limit:],
    }


@app.get("/model/status")
def model_status():
    if model_state is None:
        return {"is_trained": False, "trained_at": None, "metrics": None}
    return {
        "is_trained": True,
        "trained_at": model_state["trained_at"],
        # .get(): bundle дня 6/7 мог быть сохранён без конфигурации
        "model_type": model_state.get("model_type"),
        "hyperparameters": model_state.get("hyperparameters"),
        "metrics": model_state["metrics"],
    }
