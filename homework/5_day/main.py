from fastapi import FastAPI, HTTPException

from dataset import ChurnDataset
from model import train_churn_model
from models import FeatureVectorChurn
from preprocessing import split_info

app = FastAPI(title="ML Churn Service")

# датасет загружается один раз при старте приложения
dataset = ChurnDataset()


@app.get("/")
def get_message():
    return {"message": "ml churn service is running"}


@app.post("/predict")
def predict(features: FeatureVectorChurn):
    return features


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
    if dataset.df is None or dataset.df.empty:
        raise HTTPException(status_code=400, detail="датасет не загружен или пуст")
    _pipeline, metrics = train_churn_model(dataset.df)
    return metrics