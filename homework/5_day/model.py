import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from preprocessing import CATEGORICAL_FEATURES, NUMERIC_FEATURES, split_train_test


def build_pipeline() -> Pipeline:
    """Пайплайн: масштабирование числовых + one-hot категориальных → LogisticRegression."""
    preprocessor = ColumnTransformer([
        ("num", StandardScaler(), NUMERIC_FEATURES),
        # handle_unknown="ignore": незнакомая категория кодируется нулями, а не роняет predict
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
    ])
    return Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", LogisticRegression(max_iter=1000)),
    ])


def train_churn_model(
    df: pd.DataFrame, test_size: float = 0.2, random_state: int = 42
) -> tuple[Pipeline, dict]:
    """Обучает pipeline на train-выборке и возвращает (pipeline, метрики на test)."""
    X_train, X_test, y_train, y_test = split_train_test(df, test_size, random_state)
    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)
    metrics = {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "f1": round(float(f1_score(y_test, y_pred)), 4),
        "n_train_rows": int(len(X_train)),
        "n_test_rows": int(len(X_test)),
    }
    return pipeline, metrics
