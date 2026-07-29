class ChurnError(Exception):
    """Базовая доменная ошибка сервиса: несёт HTTP-статус, код и детали."""

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
