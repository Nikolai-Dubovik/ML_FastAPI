import pytest
from sklearn.pipeline import Pipeline

from model import build_pipeline, predict_churn, train_churn_model
from models import FeatureVectorChurn


def test_build_pipeline_has_preprocessor_and_classifier():
    pipeline = build_pipeline("random_forest", {"n_estimators": 10})

    assert isinstance(pipeline, Pipeline)
    assert [name for name, _ in pipeline.steps] == ["preprocessor", "classifier"]
    assert pipeline.named_steps["classifier"].n_estimators == 10


def test_train_churn_model_returns_metrics(sample_df):
    pipeline, metrics = train_churn_model(sample_df, "logreg", test_size=0.25)

    assert isinstance(pipeline, Pipeline)
    # точные значения зависят от данных фикстуры — проверяем диапазон, а не число
    for name in ("accuracy", "f1", "roc_auc"):
        assert 0.0 <= metrics[name] <= 1.0
    assert metrics["n_train_rows"] + metrics["n_test_rows"] == len(sample_df)


def test_predict_churn_returns_response_per_row(sample_df, features):
    pipeline, _ = train_churn_model(sample_df, "logreg", test_size=0.25)
    batch = [FeatureVectorChurn(**features), FeatureVectorChurn(**{**features, "region": "asia"})]

    responses = predict_churn(pipeline, batch)

    assert len(responses) == len(batch)
    for response in responses:
        assert response.prediction in (0, 1)
        assert set(response.probabilities) == {"0", "1"}
        assert sum(response.probabilities.values()) == pytest.approx(1.0, abs=1e-3)
