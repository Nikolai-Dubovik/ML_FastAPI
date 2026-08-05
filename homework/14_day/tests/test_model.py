import pytest

from app.ml.model import build_model, predict_churn, train_churn_model
from app.schemas import FeatureVectorChurn


def test_train_returns_metrics(synthetic_df):
    _, metrics = train_churn_model(synthetic_df)
    for name in ("accuracy", "f1", "roc_auc"):
        assert 0.0 <= metrics[name] <= 1.0
    assert metrics["n_train_rows"] + metrics["n_test_rows"] == len(synthetic_df)
    # в синтетике заложен сигнал, поэтому ранжирование заметно лучше случайного;
    # заодно ловит расчёт roc_auc по меткам вместо вероятностей (там выходит ~0.67)
    assert metrics["roc_auc"] > 0.75


def test_predict_shape_and_probabilities(synthetic_df):
    pipeline, _ = train_churn_model(synthetic_df)
    rows = synthetic_df.drop(columns=["churn"]).head(2).to_dict(orient="records")
    responses = predict_churn(pipeline, [FeatureVectorChurn(**row) for row in rows])
    assert len(responses) == 2
    for response in responses:
        assert response.prediction in (0, 1)
        assert round(sum(response.probabilities.values()), 4) == 1.0


def test_unknown_model_type():
    with pytest.raises(ValueError):
        build_model("нет такой", {})
