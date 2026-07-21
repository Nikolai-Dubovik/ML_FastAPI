from fastapi import FastAPI

from dataset import ChurnDataset
from models import FeatureVectorChurn

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