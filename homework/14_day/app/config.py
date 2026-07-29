"""Единственное место, где живут пути и настройки сервиса."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent   # .../homework/14_day/app
DAY_DIR = BASE_DIR.parent                    # .../homework/14_day

APP_TITLE = "ML Churn Service"

# путь к данным считаем по репозиторию только если переменной нет: в контейнере
# такой структуры каталогов не существует
_env_data_path = os.getenv("CHURN_DATA_PATH")
DATA_PATH = (
    Path(_env_data_path)
    if _env_data_path
    else BASE_DIR.parents[2] / "data" / "churn_dataset.csv"
)

# артефакты обучения: модель и журнал обучений
ARTIFACTS_DIR = Path(os.getenv("CHURN_ARTIFACTS_DIR", DAY_DIR / "artifacts"))
MODEL_PATH = ARTIFACTS_DIR / "churn_model.joblib"
HISTORY_PATH = ARTIFACTS_DIR / "training_history.json"
