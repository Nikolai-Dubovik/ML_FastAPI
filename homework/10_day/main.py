from fastapi import FastAPI

from dataset import ChurnDataset
from errors import ApiError, error_example, register_error_handlers
from model import predict_churn, train_churn_model
from models import FeatureVectorChurn, PredictionResponseChurn, TrainingConfigChurn
from preprocessing import feature_schema, split_info
from storage import load_churn_model, save_churn_model

app = FastAPI(title="ML Churn Service")
register_error_handlers(app)

# датасет загружается один раз при старте приложения
dataset = ChurnDataset()

# модель (bundle: pipeline + trained_at + metrics) загружается при старте, если уже обучалась
model_state: dict | None = load_churn_model()





@app.post("/predict", responses={
    409: error_example("model_not_trained", "модель ещё не обучена — вызовите POST /model/train"),
    422: error_example("validation_error", "некорректные входные данные"),
})
def predict(
    features: FeatureVectorChurn | list[FeatureVectorChurn],
) -> PredictionResponseChurn | list[PredictionResponseChurn]:
    if model_state is None:
        raise ApiError(
            409, "model_not_trained", "модель ещё не обучена — вызовите POST /model/train"
        )
    is_single = isinstance(features, FeatureVectorChurn)
    batch = [features] if is_single else features
    responses = predict_churn(model_state["pipeline"], batch)
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


@app.post("/model/train", responses={
    400: error_example("data_error", "ошибка обработки данных: неизвестный гиперпараметр"),
    422: error_example("validation_error", "некорректные входные данные"),
})
def model_train(config: TrainingConfigChurn = TrainingConfigChurn()):
    global model_state
    if dataset.df is None or dataset.df.empty:
        raise ApiError(400, "empty_dataset", "датасет не загружен или пуст")
    # ошибки sklearn (например, несуществующий гиперпараметр) ловит глобальный обработчик
    pipeline, metrics = train_churn_model(dataset.df, config.model_type, config.hyperparameters)
    model_state = save_churn_model(
        pipeline, metrics, config.model_type, config.hyperparameters
    )
    return {
        "model_type": config.model_type,
        "hyperparameters": config.hyperparameters,
        "metrics": metrics,
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