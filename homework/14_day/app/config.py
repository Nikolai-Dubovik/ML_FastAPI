from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # homework/14_day
DATA_PATH = BASE_DIR.parents[1] / "data" / "churn_dataset.csv"
ARTIFACTS_DIR = BASE_DIR / "artifacts"
MODEL_PATH = ARTIFACTS_DIR / "churn_model.joblib"
# журнал лежит рядом с артефактом модели, но независим от него
HISTORY_PATH = ARTIFACTS_DIR / "training_history.json"
