"""Доменные исключения сервиса и глобальные обработчики ошибок."""

import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.schemas import ErrorResponse

logger = logging.getLogger("churn.errors")


class ChurnError(Exception):
    """Базовая доменная ошибка: несёт HTTP-статус, код и детали."""

    status_code = 500
    code = "internal_error"

    def __init__(self, message: str, details: dict | list | str | None = None):
        super().__init__(message)
        self.message = message
        self.details = details


class ModelNotTrainedError(ChurnError):
    """Запрос корректен, но модель ещё не обучена — конфликт состояния."""

    status_code = 409
    code = "model_not_trained"


class EmptyDatasetError(ChurnError):
    """Датасет не загружен или пуст — обучать не на чем."""

    status_code = 400
    code = "empty_dataset"


class TrainingError(ChurnError):
    """Обучение не удалось: обычно плохой тип модели или гиперпараметр."""

    status_code = 400
    code = "training_failed"


# описания ошибок для /docs
ERROR_RESPONSES = {
    400: {"model": ErrorResponse, "description": "пустой датасет или ошибка обучения"},
    409: {"model": ErrorResponse, "description": "модель ещё не обучена"},
    422: {"model": ErrorResponse, "description": "ошибка валидации входных данных"},
}

# /predict принимает union (один объект или список), и pydantic вставляет в loc
# имя варианта — клиенту оно не нужно
UNION_BRANCHES = {"FeatureVectorChurn", "list[FeatureVectorChurn]"}


def error_response(status_code: int, code: str, message: str, details=None) -> JSONResponse:
    """Единый формат тела ошибки для всех обработчиков."""
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "details": details}},
    )


def validation_errors(exc: RequestValidationError) -> list[dict]:
    """Разворачивает ошибки pydantic в компактный список field / type / message."""
    errors = []
    for err in exc.errors():
        # loc = ("body", "monthly_fee") или ("body", "FeatureVectorChurn", "monthly_fee")
        parts = [str(part) for part in err["loc"][1:] if str(part) not in UNION_BRANCHES]
        if not parts:
            # ошибка от неподошедшего варианта union («это не список») — шум
            continue
        errors.append({"field": ".".join(parts), "type": err["type"], "message": err["msg"]})
    if not errors:
        # тело целиком не то (например, прислали строку) — конкретных полей нет
        errors = [
            {"field": "body", "type": err["type"], "message": err["msg"]}
            for err in exc.errors()
        ]
    return errors


def register_error_handlers(app: FastAPI) -> None:
    """Вешает обработчики, дающие единый JSON-формат ошибки вместо трассировок."""

    @app.exception_handler(ChurnError)
    def handle_churn_error(request: Request, exc: ChurnError) -> JSONResponse:
        logger.warning("%s %s → %s: %s", request.method, request.url.path, exc.code, exc.message)
        return error_response(exc.status_code, exc.code, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    def handle_validation_error(request: Request, exc: RequestValidationError) -> JSONResponse:
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
        # трассировка нужна в логе, но не в ответе клиенту
        logger.exception("%s %s → internal_error", request.method, request.url.path)
        return error_response(500, "internal_error", "внутренняя ошибка сервиса")
