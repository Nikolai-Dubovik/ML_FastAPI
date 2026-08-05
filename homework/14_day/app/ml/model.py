import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from app.ml.preprocessing import (
    CATEGORICAL_FEATURES,
    NUMERIC_FEATURES,
    features_to_dataframe,
    split_train_test,
)
from app.schemas import FeatureVectorChurn, PredictionResponseChurn


def build_model(model_type: str, hyperparameters: dict):
    """Создаёт классификатор по типу; дефолты можно переопределить гиперпараметрами."""
    if model_type == "logreg":
        return LogisticRegression(**{"max_iter": 1000, **hyperparameters})
    if model_type == "random_forest":
        return RandomForestClassifier(**{"random_state": 42, **hyperparameters})
    raise ValueError(f"неизвестный тип модели: {model_type}")


def build_pipeline(model_type: str = "logreg", hyperparameters: dict | None = None) -> Pipeline:
    """Пайплайн: масштабирование числовых + one-hot категориальных → выбранная модель."""
    preprocessor = ColumnTransformer([
        ("num", StandardScaler(), NUMERIC_FEATURES),
        # handle_unknown="ignore": незнакомая категория кодируется нулями, а не роняет predict
        ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
    ])
    return Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", build_model(model_type, hyperparameters or {})),
    ])


def train_churn_model(
    df: pd.DataFrame,
    model_type: str = "logreg",
    hyperparameters: dict | None = None,
    test_size: float = 0.2,
    random_state: int = 42,
) -> tuple[Pipeline, dict]:
    """Обучает pipeline на train-выборке и возвращает (pipeline, метрики на test)."""
    X_train, X_test, y_train, y_test = split_train_test(df, test_size, random_state)
    pipeline = build_pipeline(model_type, hyperparameters)
    pipeline.fit(X_train, y_train)
    y_pred = pipeline.predict(X_test)
    y_proba = pipeline.predict_proba(X_test)[:, 1]  # вероятность класса «уйдёт»
    metrics = {
        "accuracy": round(float(accuracy_score(y_test, y_pred)), 4),
        "f1": round(float(f1_score(y_test, y_pred)), 4),
        # roc_auc считается по вероятностям, а не по меткам
        "roc_auc": round(float(roc_auc_score(y_test, y_proba)), 4),
        "n_train_rows": int(len(X_train)),
        "n_test_rows": int(len(X_test)),
    }
    return pipeline, metrics


def predict_churn(
    pipeline: Pipeline, features: list[FeatureVectorChurn]
) -> list[PredictionResponseChurn]:
    """Предсказывает класс churn и вероятности классов для списка клиентов."""
    X = features_to_dataframe(features)  # тот же набор и порядок колонок, что при обучении
    predictions = pipeline.predict(X)
    probabilities = pipeline.predict_proba(X)
    return [
        PredictionResponseChurn(
            prediction=int(pred),
            # порядок колонок в predict_proba задаёт pipeline.classes_
            probabilities={
                str(int(cls)): round(float(p), 4)
                for cls, p in zip(pipeline.classes_, proba_row)
            },
        )
        for pred, proba_row in zip(predictions, probabilities)
    ]
