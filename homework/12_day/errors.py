from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# именно из starlette: иначе 404 от самого фреймворка пройдут мимо обработчика
from starlette.exceptions import HTTPException


class ApiError(HTTPException):
    """HTTPException с машиночитаемым кодом ошибки."""

    def __init__(self, status_code: int, code: str, message: str):
        super().__init__(status_code=status_code, detail=message)
        self.code = code


def error_response(
    status_code: int, code: str, message: str, details: list | None = None
) -> JSONResponse:
    """Единственное место, где зашит формат ошибки: code / message / details."""
    return JSONResponse(
        status_code=status_code,
        content={"error": {"code": code, "message": message, "details": details or []}},
    )


def error_example(code: str, message: str) -> dict:
    """Пример ошибки для responses={...} в Swagger."""
    return {"content": {"application/json": {"example": {
        "error": {"code": code, "message": message, "details": []},
    }}}}


def register_error_handlers(app: FastAPI) -> None:
    """Регистрирует глобальные обработчики — клиент всегда получает единый формат."""

    @app.exception_handler(HTTPException)
    def handle_http_error(request, exc: HTTPException):
        # у чужих HTTPException (404 от FastAPI) поля code нет
        return error_response(exc.status_code, getattr(exc, "code", "http_error"), exc.detail)

    @app.exception_handler(RequestValidationError)
    def handle_validation_error(request, exc: RequestValidationError):
        # loc[1:] — отбрасываем первый элемент "body", остаётся имя поля
        details = [
            {"field": ".".join(str(p) for p in e["loc"][1:]), "message": e["msg"]}
            for e in exc.errors()
        ]
        return error_response(422, "validation_error", "некорректные входные данные", details)

    @app.exception_handler(ValueError)
    @app.exception_handler(TypeError)
    def handle_data_error(request, exc: Exception):
        # сюда попадают ошибки pandas/sklearn при подготовке данных, обучении и предсказании
        return error_response(400, "data_error", f"ошибка обработки данных: {exc}")

    @app.exception_handler(Exception)
    def handle_internal_error(request, exc: Exception):
        return error_response(500, "internal_error", "внутренняя ошибка сервиса")
