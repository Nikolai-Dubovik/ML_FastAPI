from fastapi import FastAPI, HTTPException

from dataset import ChurnDataset
from model import predict_churn, train_churn_model
from models import FeatureVectorChurn, PredictionResponseChurn
from preprocessing import split_info
from storage import load_churn_model, save_churn_model

app = FastAPI(title="ML Churn Service")

# датасет загружается один раз при старте приложения
dataset = ChurnDataset()

# модель (bundle: pipeline + trained_at + metrics) загружается при старте, если уже обучалась
model_state: dict | None = load_churn_model()


@app.get("/")
def get_message():
    return {"message": "ml churn service is running"}


@app.post("/predict")
def predict(features: FeatureVectorChurn | list[FeatureVectorChurn],) -> PredictionResponseChurn | list[PredictionResponseChurn]:
    if model_state is None:
        raise HTTPException(
            status_code=400, detail="модель ещё не обучена — вызовите POST /model/train"
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


@app.post("/model/train")
def model_train():
    global model_state
    if dataset.df is None or dataset.df.empty:
        raise HTTPException(status_code=400, detail="датасет не загружен или пуст")
    pipeline, metrics = train_churn_model(dataset.df)
    model_state = save_churn_model(pipeline, metrics)
    return metrics


@app.get("/model/status")
def model_status():
    if model_state is None:
        return {"is_trained": False, "trained_at": None, "metrics": None}
    return {
        "is_trained": True,
        "trained_at": model_state["trained_at"],
        "metrics": model_state["metrics"],
    }