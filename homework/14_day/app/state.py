from app.ml.dataset import ChurnDataset
from app.ml.storage import load_churn_model

# датасет загружается один раз при старте приложения
dataset = ChurnDataset()

# модель (bundle: pipeline + trained_at + metrics) загружается при старте, если уже обучалась
model_state: dict | None = load_churn_model()
